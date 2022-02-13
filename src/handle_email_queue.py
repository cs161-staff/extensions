from typing import List

from src.assignments import AssignmentList
from src.email import Email
from src.errors import ConfigurationError
from src.gradescope import Gradescope
from src.record import EMAIL_STATUS_IN_QUEUE, StudentRecord
from src.sheets import SHEET_ASSIGNMENTS, SHEET_ENVIRONMENT_VARIABLES, SHEET_STUDENT_RECORDS, BaseSpreadsheet
from src.slack import SlackManager
from src.utils import Environment


def handle_email_queue(request_json):
    if "spreadsheet_url" not in request_json:
        raise ConfigurationError("handle_email_queue expects spreadsheet_url parameter")

    # Get pointers to sheets.
    base = BaseSpreadsheet(spreadsheet_url=request_json["spreadsheet_url"])
    sheet_assignments = base.get_sheet(SHEET_ASSIGNMENTS)
    sheet_records = base.get_sheet(SHEET_STUDENT_RECORDS)
    sheet_env_vars = base.get_sheet(SHEET_ENVIRONMENT_VARIABLES)

    # Set up environment variables.
    Environment.configure_env_vars(sheet_env_vars)

    # Fetch assignments.
    assignments = AssignmentList(sheet=sheet_assignments)

    # Fetch all students.
    emails: List[str] = []

    slack = SlackManager()

    for i, table_record in enumerate(sheet_records.get_all_records()):
        student = StudentRecord(table_index=i, table_record=table_record, sheet=sheet_records)
        if student.email_status() == EMAIL_STATUS_IN_QUEUE:
            # Guard around the outbound email, so we can diagnose errors easily and keep state consistent.
            try:
                email = Email.from_student_record(student=student, assignments=assignments)
                email.send()
                student.set_status_email_approved()
                student.flush()
                emails.append(student.get_email())
            except Exception as err:
                slack.add_warning(
                    f"Attempted to send an email to {student.get_email()}, but failed.\n"
                    + "Please follow up with this student manually and/or check email logs.\n"
                    + "If this is a spreadsheet error, correct the error, and re-run email queue processor.\n"
                    + "Error: "
                    + str(err)
                )

            if Gradescope.is_enabled():
                client = Gradescope()
                warnings = student.apply_extensions(assignments=assignments, gradescope=client)
                for warning in warnings:
                    slack.add_warning(warning)

    if len(emails) == 0:
        slack.send_message("Sent zero emails from the queue...was it empty?")
    else:
        slack.send_message(
            f"Sent {len(emails)} emails from the queue. Emails: " + "\n" + "```" + "\n".join(emails) + "\n" + "```"
        )
