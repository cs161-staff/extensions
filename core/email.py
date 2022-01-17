from typing import Dict, Any
import datetime
from dateutil import parser
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from tabulate import tabulate
from markdown2 import Markdown
import gspread

from core.constants import EMAIL_AUTO_SENT, EMAIL_IN_QUEUE
from core.sheets import extract_config, extract_headers, extract_records, fetch_table


def send_email_sendgrid(from_email: str, to_email: str, cc_email: str, reply_to: str, subject: str, content: str):

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )
    message.add_cc(cc_email)
    message.reply_to = reply_to
    print("TODO: Bring email back in.")
    # try:
    #     sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    #     sg.send(message)
    # except Exception as e:
    #     print(message)
    #     print(e.body)


def process_email_queue(request_json):
    # Get a handle to the spreadsheet.
    gc = gspread.service_account("service-account.json")
    spreadsheet = gc.open_by_url(request_json["spreadsheet_url"])

    # Pull configuration variables
    config = extract_config(fetch_table(spreadsheet=spreadsheet, name="Configuration"))

    # Extract student records.
    table = fetch_table(spreadsheet=spreadsheet, name="All Extensions")
    headers = extract_headers(table=table)
    records = extract_records(table=table, index_by="sid", include_row_number=True)

    # Pull the assignment configuration table
    all_assignments = extract_records(
        fetch_table(spreadsheet=spreadsheet, name="Assignments"), index_by="name", include_row_number=False
    )

    # TODO: This is copied from form.py, so abstract away into a StudentRecord object.
    def update_student_record(write_back_index, write_back):
        master_table = spreadsheet.worksheet("All Extensions")
        for column_key, value in write_back.items():
            # One-indexed, and skip header, so add two
            row_index = write_back_index + 2
            # One-indexed, so add one
            column_index = headers[column_key] + 1
            master_table.update_cell(row_index, column_index, value)

    # For each record, check if the email category is equal to In Queue
    for i, record in records.values():
        if record["email_status"] == EMAIL_IN_QUEUE:
            print('Sending email for:', record['sid'])
            send_email(record=record, all_assignments=all_assignments, config=config)
            write_back = {"email_status": EMAIL_AUTO_SENT}
            print('Writing data back...')
            update_student_record(write_back_index=i, write_back=write_back)


def send_email(record: Dict[str, Any], all_assignments: Dict[str, Any], config: Dict[str, Any]):

    signature = config["signature"]

    prefix = ""
    prefix += f"Hi {record['name']},"
    prefix += "\n\n"
    prefix += "You recently requested an extension for an assignment. We've processed this extension, and here are your updated due dates:"
    prefix += "\n\n"

    fmt_date = lambda dt: dt.strftime("%A, %B %-d")

    headers = ["Assignment", "Originally Due", "Now Due", "Days Extended"]
    rows = []

    for assignment in all_assignments.values():
        assignment_id = assignment["id"]
        num_days = record[assignment_id]

        if num_days:
            original_due_date = parser.parse(assignment["due_date"])
            new_due_date = original_due_date + datetime.timedelta(days=int(num_days))
            if record[assignment_id]:
                rows.append([assignment["name"], fmt_date(original_due_date), fmt_date(new_due_date), num_days])

    suffix = ""
    suffix += "\n\n"
    if record["email_comments"]:
        suffix += "Additional comments: " + "*" + record["email_comments"] + "*" + "\n\n"

    suffix += "If something doesn't look right, please reply to this email!"
    suffix += "\n\n"
    suffix += "Best,"
    suffix += "\n\n"
    suffix += signature

    email = ""
    email += Markdown().convert(prefix)
    email += tabulate(rows, headers=headers, tablefmt="html", colalign=("left", "left", "left", "left"))
    email += Markdown().convert(suffix)

    send_email_sendgrid(
        from_email=config["from"],
        to_email=record["email"],
        cc_email=config["cc"],
        reply_to=config["reply-to"],
        subject=config["subject"],
        content=Markdown().convert(email),
    )
