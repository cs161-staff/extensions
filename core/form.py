from typing import Any, Dict
from core.constants import (
    AUTO_APPROVAL_THRESHOLD,
    EMAIL_AUTO_SENT,
    EMAIL_PENDING_APPROVAL,
    STATUS_AUTO_APPROVED,
    STATUS_PENDING,
)
from core import email, slack
from core.errors import InternalError, UserError
from core.sheets import extract_config, extract_headers, extract_records, fetch_table
from gspread.spreadsheet import Spreadsheet
import gspread
from core.utils import cast_bool, cast_int, cast_list


def preprocess_form_response(spreadsheet: Spreadsheet, form_response: Dict[str, Any]):
    table = fetch_table(spreadsheet=spreadsheet, name="Questions")
    question_map = extract_config(table=table)
    transformed_response: Dict[str, Any] = {}
    for question, question_response in form_response.items():
        response = question_response[0]
        if question not in question_map:
            raise InternalError("Mismatch between form questions and question map.")
        transformed_response[question_map[question]] = response
    return transformed_response


def handle_form_submit(request_json: Dict[str, Any]):
    # Get a handle to the spreadsheet.
    gc = gspread.service_account("service-account.json")
    spreadsheet_url = request_json["spreadsheet_url"]
    spreadsheet = gc.open_by_url(spreadsheet_url)
    form_data = request_json["form_data"]

    # Transform the response into the format that we want.
    form = preprocess_form_response(spreadsheet=spreadsheet, form_response=form_data)

    # Pull the assignment configuration table
    all_assignments = extract_records(
        fetch_table(spreadsheet=spreadsheet, name="Assignments"), index_by="name", include_row_number=False
    )

    # Pull configuration variables
    config = extract_config(fetch_table(spreadsheet=spreadsheet, name="Configuration"))

    # Extract the student record and row index.
    table = fetch_table(spreadsheet=spreadsheet, name="Roster")
    headers = extract_headers(table=table)
    records = extract_records(table=table, index_by="sid")

    sid = form["sid"]
    if sid not in records:
        raise InternalError(f"Student-entered SID ({sid}) does not match SID in roster.")

    # This is the record for the student. We can use the row_index item to refer back to it.
    write_back_index, student_record = records[sid]

    approval_status = student_record["approval_status"]

    # Dump columns to write back to the student record row here.
    write_back = {}

    print(f"Processing form response for {sid}...")

    if cast_bool(form["knows_assignments"]):
        assignments = cast_list(form["assignments"])
        requested_days = cast_list(form["days"])
        if len(assignments) != len(requested_days):
            raise UserError("User provided invalid assignment/day combo: # assignments != # days.")

        for num_days, assignment_name in zip(requested_days, assignments):
            num_days = cast_int(num_days)

            print(f"[{assignment_name}] Processing extension request of {num_days}.")

            assignment_id = all_assignments[assignment_name]["id"]

            if student_record[assignment_id]:
                print(f"[{assignment_name}] WARNING: Overwriting existing request in-place.")

            write_back[assignment_id] = num_days

            if num_days <= AUTO_APPROVAL_THRESHOLD:
                print(f"[{assignment_name}] This request is under the auto-approval threshold.")
                if approval_status != STATUS_PENDING:
                    print(f"[{assignment_name}] Request has been auto-approved.")
                    approval_status = STATUS_AUTO_APPROVED
                else:
                    print(f"[{assignment_name}] Student has other pending requests. Needs human.")
                    approval_status = STATUS_PENDING
            else:
                print(f"[{assignment_name}] Student requested more days than threshold. Needs human.")
                approval_status = STATUS_PENDING

    write_back["approval_status"] = approval_status

    if write_back["approval_status"] == STATUS_AUTO_APPROVED:
        print("Sending email...")
        email.send_email(record=student_record, all_assignments=all_assignments, config=config)
        write_back["email_status"] = EMAIL_AUTO_SENT
        slack.send_auto_approved(student_record=student_record, form=form)
    else:
        slack.send_needs_manual_approval(spreadsheet_url=spreadsheet_url, student_record=student_record, form=form, all_assignments=all_assignments)
        write_back["email_status"] = EMAIL_PENDING_APPROVAL

    master_table = spreadsheet.worksheet("Roster")
    for column_key, value in write_back.items():
        # One-indexed, and skip header, so add two
        row_index = write_back_index + 2
        # One-indexed, so add one
        column_index = headers[column_key] + 1
        master_table.update_cell(row_index, column_index, value)
