from enum import auto
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
    student = StudentRecord.from_sid(sid=submission.get_sid(), sheet_records=sheet_records)

    # Get a pointer to Slack, and set the current student
    slack = SlackManager()
    slack.set_current_student(submission=submission, student=student, assignment_manager=assignment_manager)

    needs_human = False

    # TODO: Configure this into the auto-approve logic as desired.
    # num_existing_requests = student.existing_request_count()

    if submission.knows_assignments():
        print("Student requested extension for specific assignments.")
        print("Checking for partner...")
        if submission.has_partner():
            print("Attempting to look up partner by SID.")
            partner = StudentRecord.from_sid(sid=submission.get_partner_sid(), sheet_records=sheet_records)
        else:
            partner = None

        # Walk through all of this student's form-provided extension requests. If any of them trigger a manual approval,
        # then the entire record becomes flagged for manual approval. If the student has already been flagged for
        # manual approval or a student support meeting, then we don't change that status. Only if these two things are
        # false do we trigger an "auto-approval" - and it's in this last case that the student automatically recieves
        # an email.
        for assignment_id, num_days in submission.get_requests(assignment_manager=assignment_manager).items():
            print(f"[{assignment_id}] Processing request for {num_days} days.")

            existing_request = student.get_assignment(assignment_id=assignment_id)
            if existing_request:
                print(f"[{assignment_id}] Request already exists for {existing_request} days. Needs manual approval.")
                needs_human = True
            elif num_days > Environment.get_auto_approve_threshold():
                print(f"[{assignment_id}] Request is > auto-approve threshold. Needs manual approval.")
                needs_human = True
            else:
                print(f"[{assignment_id}] Request meets criteria for auto-approval.")

            student.queue_write_back(col_key=assignment_id, col_value=num_days)

            # Queue up the extension of num_days for the partner as well.
            if assignment_manager.is_partner_assignment(assignment_id) and submission.has_partner():
                partner.queue_write_back(col_key=assignment_id, col_value=num_days)

        # And finally: the conclusion. Figure out what to set the status to, and send corresponding Slack/emails.
        if (
            student.approval_status() == APPROVAL_STATUS_REQUESTED_MEETING
            or student.approval_status() == APPROVAL_STATUS_PENDING
        ):
            # Student has a pending extension or meeting request, so not updating approval.

            # For student: write back only num_day updates.
            student.dispatch_writes()

            # For partner: write back new statuses (PENDING) and num_day updates.
            if partner:
                partner.queue_approval_status(APPROVAL_STATUS_PENDING)
                partner.queue_email_status(EMAIL_STATUS_PENDING)
                partner.dispatch_writes()

            slack.send_student_update(
                "An extension request could not be auto-approved (existing request in progress). Details:"
            )

        elif submission.has_partner() and (
            partner.approval_status() == APPROVAL_STATUS_REQUESTED_MEETING
            or partner.approval_status() == APPROVAL_STATUS_PENDING
        ):
            # Partner has a pending extension or meeting request, so not updating approval.

            # For partner: write back only num_day updates.
            partner.dispatch_writes()

            # For student: write back new statuses (PENDING) and num_day updates.
            student.queue_approval_status(APPROVAL_STATUS_PENDING)
            student.queue_email_status(EMAIL_STATUS_PENDING)
            student.dispatch_writes()

            slack.send_student_update(
                "An extension request could not be auto-approved (blocked by an existing request in progress for the student's partner). Details:"
            )

        else:
            if needs_human:
                # Don't auto-approve the request
                def apply(user: StudentRecord):
                    user.queue_approval_status(APPROVAL_STATUS_PENDING)
                    user.queue_email_status(EMAIL_STATUS_PENDING)
                    user.dispatch_writes()

                apply(student)
                if partner:
                    apply(partner)

                slack.send_student_update(
                    "An extension request could not be auto-approved (failed to meet the approval criteria). Details:"
                )

            else:
                # Auto-approve the request, and send out emails.
                # If the student has a partner, auto-approve for them as well and send out emails for them.

                def apply(user: StudentRecord):
                    user.queue_approval_status(APPROVAL_STATUS_AUTO_APPROVED)
                    user.queue_email_status(EMAIL_STATUS_AUTO_SENT)
                    user.dispatch_writes()

                def send_email(user: StudentRecord):
                    # Guard around the outbound email, so we can diagnose errors easily and keep state consistent.
                    try:
                        email = Email.from_student_record(student=student, assignment_manager=assignment_manager)
                        email.send()
                    except Exception as err:
                        raise KnownError(
                            "Writes to spreadsheet succeed, but email to student failed.\n"
                            + "Please follow up with this student manually and/or check SendGrid logs.\n"
                            + "Error: "
                            + str(err)
                        )

                apply(student)
                send_email(student)

                if partner:
                    apply(partner)
                    send_email(partner)

                slack.send_student_update("An extension request was automatically approved!", autoapprove=True)

    else:
        print("Student requested general extension without specific assignments...")
        student.queue_approval_status(APPROVAL_STATUS_REQUESTED_MEETING)
        student.dispatch_writes()
        slack.send_student_update("*[Action Required]* A student requested a student support meeting.")
