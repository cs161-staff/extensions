from src.email import Email
from src.assignments import AssignmentManager
from src.errors import ConfigurationError, KnownError
from src.record import EMAIL_STATUS_AUTO_SENT, EMAIL_STATUS_IN_QUEUE, StudentRecord
from src.sheets import (
    SHEET_ASSIGNMENTS,
    SHEET_ENVIRONMENT_VARIABLES,
    SHEET_FORM_QUESTIONS,
    SHEET_STUDENT_RECORDS,
    BaseSpreadsheet,
)
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
    assignment_manager = AssignmentManager(sheet=sheet_assignments)

    # Fetch all students.
    sent_count = 0
    emails = []

    for i, table_record in enumerate(sheet_records.get_all_records()):
        student = StudentRecord(table_index=i, table_record=table_record, sheet=sheet_records)
        if student.email_status() == EMAIL_STATUS_IN_QUEUE:
            # Guard around the outbound email, so we can diagnose errors easily and keep state consistent.
            try:
                email = Email.from_student_record(student=student, assignment_manager=assignment_manager)
                emails.append(student.get_email())
                email.send()
                student.set_status_email_approved()
                student.dispatch_writes()
                sent_count += 1
            except Exception as err:
                raise KnownError(
                    f"Attempted to send an email to {student.get_email()}, but failed.\n"
                    + "Please follow up with this student manually and/or check email logs.\n"
                    + "If this is a spreadsheet error, correct the error, and re-run email queue processor.\n"
                    + "Error: "
                    + str(err)
                )

    slack = SlackManager()
    if len(emails) == 0:
        slack.send_message("Sent zero emails from the queue...was it empty?")
    else:
        slack.send_message(
            f"Sent {sent_count} emails from the queue. Emails: " + "\n" + "```" + "\n".join(emails) + "\n" + "```"
        )
