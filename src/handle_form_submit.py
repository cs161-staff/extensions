from src import submission
from src.assignments import AssignmentManager
from src.email import Email
from src.errors import ConfigurationError, FormInputError, KnownError
from src.record import (
    APPROVAL_STATUS_AUTO_APPROVED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REQUESTED_MEETING,
    EMAIL_STATUS_AUTO_SENT,
    EMAIL_STATUS_PENDING,
    StudentRecord,
)
from src.slack import SlackManager
from src.submission import FormSubmission
from src.utils import Environment
from src.sheets import (
    SHEET_ASSIGNMENTS,
    SHEET_ENVIRONMENT_VARIABLES,
    SHEET_FORM_QUESTIONS,
    SHEET_STUDENT_RECORDS,
    BaseSpreadsheet,
)

# TODO: What about retroactive extensions?


def handle_form_submit(request_json):
    if "spreadsheet_url" not in request_json or "form_data" not in request_json:
        raise ConfigurationError("handle_form_submit expects spreadsheet_url/form_data parameters")

    # Get pointers to sheets.
    base = BaseSpreadsheet(spreadsheet_url=request_json["spreadsheet_url"])
    sheet_assignments = base.get_sheet(SHEET_ASSIGNMENTS)
    sheet_records = base.get_sheet(SHEET_STUDENT_RECORDS)
    sheet_form_questions = base.get_sheet(SHEET_FORM_QUESTIONS)
    sheet_env_vars = base.get_sheet(SHEET_ENVIRONMENT_VARIABLES)

    # Set up environment variables.
    Environment.configure_env_vars(sheet_env_vars)

    # Fetch assignments.
    assignment_manager = AssignmentManager(sheet=sheet_assignments)

    # Fetch form submission.
    submission = FormSubmission(form_payload=request_json["form_data"], question_sheet=sheet_form_questions)

    # Extract this student's record.
    query_result = sheet_records.get_record_by_id(id_column="sid", id_value=submission.get_sid())
    if not query_result:
        raise FormInputError(f"This student's SID was not found (sid: {submission.get_sid()}).")
    student = StudentRecord(table_index=query_result[0], table_record=query_result[1], sheet=sheet_records)

    # Get a pointer to Slack, and set the current student
    slack = SlackManager()
    slack.set_current_student(submission=submission, student=student, assignment_manager=assignment_manager)

    # Core logic goes here.
    log_records = []

    def log(msg: str):
        print(msg)
        log_records.append(msg)

    needs_human = False

    # TODO: Configure this into the auto-approve logic as desired.
    # num_existing_requests = student.existing_request_count()

    if submission.knows_assignments():
        log("Student requested extension for specific assignments. Processing each one...")

        # Walk through all of this student's form-provided extension requests. If any of them trigger a manual approval,
        # then the entire record becomes flagged for manual approval. If the student has already been flagged for
        # manual approval or a student support meeting, then we don't change that status. Only if these two things are
        # false do we trigger an "auto-approval" - and it's in this last case that the student automatically recieves
        # an email.
        for assignment_id, num_days in submission.get_requests(assignment_manager=assignment_manager).items():
            log(f"[{assignment_id}] Processing request for {num_days} days.")

            existing_request = student.get_assignment(assignment_id=assignment_id)
            if existing_request:
                log(f"[{assignment_id}] Request already exists for {existing_request} days. Needs manual approval.")
                needs_human = True
            elif num_days > Environment.get_auto_approve_threshold():
                log(f"[{assignment_id}] Request is > auto-approve threshold. Needs manual approval.")
                needs_human = True
            else:
                log(f"[{assignment_id}] Request meets criteria for auto-approval.")
                
            student.queue_write_back(col_key=assignment_id, col_value=num_days)

        # And finally: the conclusion. Figure out what to set the status to, and send corresponding Slack/emails.
        if student.approval_status() == APPROVAL_STATUS_REQUESTED_MEETING:
            # Student has a pending meeting request, so not updating approval.
            student.dispatch_writes()
            slack.send_student_update("*[Action Required]* A student with a pending support meeting submitted an extension request, so the request could not be approved automatically!")

        elif student.approval_status() == APPROVAL_STATUS_PENDING:
            # Student has a pending extension request, so not auto-approving even if this request is approvable.
            student.dispatch_writes()
            slack.send_student_update("*[Action Required]* A student with pending extension requests submitted another extension request, so the request could not be approved automatically!")

        else:
            if needs_human:
                # Don't auto-approve the request
                student.queue_approval_status(APPROVAL_STATUS_PENDING)
                student.queue_email_status(EMAIL_STATUS_PENDING)
                student.dispatch_writes()
                slack.send_student_update("*[Action Required]* An extension request could not be auto-approved!")

            else:
                # Auto-approve the request
                student.queue_approval_status(APPROVAL_STATUS_AUTO_APPROVED)
                student.queue_email_status(EMAIL_STATUS_AUTO_SENT)

                student.dispatch_writes()

                # Guard around the outbound email, so we can diagnose errors easily and keep state consistent.
                try:
                    email = Email.from_student_record(student=student, assignment_manager=assignment_manager)
                    email.preview()
                except Exception as err:
                    raise KnownError(
                        "Writes to spreadsheet succeed, but email to student failed.\n"
                        + "Please follow up with this student manually and/or check SendGrid logs.\n"
                        + "Error: "
                        + str(err)
                    )
                slack.send_student_update("An extension request was automatically approved!")

    else:
        log("Student requested general extension without specific assignments...")
        student.queue_approval_status(APPROVAL_STATUS_REQUESTED_MEETING)
        student.dispatch_writes()
        slack.send_student_update("*[Action Required]* A student requested a student support meeting.")
