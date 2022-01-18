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

    # -----------------------------------------------------------------------------------------------------------------
    # Section 0: Setup.
    # -----------------------------------------------------------------------------------------------------------------

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

    # -----------------------------------------------------------------------------------------------------------------
    # Section 1: The student submitted a general plea for help.
    # -----------------------------------------------------------------------------------------------------------------
    if not submission.knows_assignments():
        print("Student requested general extension without specific assignments...")
        student.set_status_requested_meeting()
        student.dispatch_writes()
        slack.send_student_update("*[Action Required]* A student requested a student support meeting. Details:")
        return

    # -----------------------------------------------------------------------------------------------------------------
    # Section 2A: The student submitted an extension for one or more assignments; process each extension request.
    #
    # Here, we check to make sure each extension qualifies for auto-approve status. If one of them fails to qualify,
    # then we can't auto-approve this transaction as a whole; we flag the whole record for manual approval.
    # -----------------------------------------------------------------------------------------------------------------
    print("Student requested extension for specific assignments.")
    needs_human = False
    partner = None

    if submission.has_partner():
        print("Attempting to look up partner by SID.")
        partner = StudentRecord.from_sid(sid=submission.get_partner_sid(), sheet_records=sheet_records)

    for assignment_id, num_days in submission.get_requests(assignment_manager=assignment_manager).items():
        print(f"[{assignment_id}] Processing request for {num_days} days.")

        # Flag Case 1: The student has an existing request for this particular assignment.
        existing_request = student.get_assignment(assignment_id=assignment_id)
        if existing_request:
            needs_human = (
                f"for `{assignment_id}`, an existing request of {existing_request} days was "
                + "overwritten by a new request for an extension of {num_days} days"
            )

        # Flag Case #2: The number of requested days is too large (non-DSP).
        elif not submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold():
            needs_human = f"a request of {num_days} days is greater than auto-approve threshold"

        # Flag Case #3: The number of requested days is too large (DSP).
        elif submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold_dsp():
            needs_human = f"a DSP request of {num_days} days is greater than DSP auto-approve threshold"

        # TODO: Add other flag cases here (e.g. total # extensions is >= 6, or something like that...)

        # Passed all cases, so proceed.
        else:
            print(f"[{assignment_id}] Request meets criteria for auto-approval.")

        # Regardless of whether or not this needs a human, we write the number of days requested back onto the
        # roster sheet (this is in a queue-style format, where we queue up these writes and then batch-process
        # them all at the end).
        student.queue_write_back(col_key=assignment_id, col_value=num_days)

        # We do the same for the partner, if this assignment has a partner and the submission has a partner.
        if assignment_manager.is_partner_assignment(assignment_id) and submission.has_partner():
            partner.queue_write_back(col_key=assignment_id, col_value=num_days)

        # Aside: if the form submission claims DSP, but the student record isn't marked as DSP, then flag it
        if submission.claims_dsp() and not student.is_dsp():
            slack.send_message(
                "Note: a student claimed DSP status on their extension request but is not marked "
                + f"as DSP in our roster (student: {student.get_email()}). Please investigate."
            )

    # -----------------------------------------------------------------------------------------------------------------
    # Section 2B: We finished processing all extensions, so let's see what we should set the final "status" column to.
    #
    # Here, we check to make sure the status for the student and the partner are not a "work-in-progress" - that is,
    # there isn't existing work (e.g. a student meeting, or some other extension request) happening in the row.
    # -----------------------------------------------------------------------------------------------------------------

    # Case (1): Submission contains partner, and student's status is a "work-in-progress".
    # We can't auto-approve here for either party (we're blocked on the student).
    if submission.has_partner() and student.has_wip_status():
        student.dispatch_writes()
        partner.set_status_pending()
        partner.dispatch_writes()
        slack.send_student_update(
            "An extension request could not be auto-approved (existing request in progress). "
            + "Updated status for partner, but left student status as is. "
            + "Details:"
        )

    # Case (2): Submission contains partner, and partner's status is a "work-in-progress"
    # We can't auto-approve here for either party (we're blocked on the partner).
    elif submission.has_partner() and partner.has_wip_status():
        partner.dispatch_writes()
        student.set_status_pending()
        student.dispatch_writes()

        slack.send_student_update(
            "An extension request could not be auto-approved. "
            + "Updated status for student, but left partner status as is. "
            + "Details:"
        )

    # Case (3): Submission doesn't contain partner, and student's status is a "work-in-progress"
    # Here, we don't want to touch the student's status (e.g. if it's "Meeting Requested", we want to leave
    # it as such). But we do want to update the roster with the number of days requested, so we dispatch writes.
    elif student.has_wip_status():
        student.dispatch_writes()
        slack.send_student_update("An extension request could not be auto-approved. Details:")

    # Case (4): Student's status (and, if applicable, partner's status) are "clean" - there is no pending
    # activity in either of these rows, so we can go ahead and check if the extension as a whole qualifies
    # for auto-approval. In this case, it doesn't -- it needs a human!
    elif needs_human:
        student.set_status_pending()
        student.dispatch_writes()

        if partner:
            partner.set_status_pending()
            partner.dispatch_writes()

        slack.send_student_update(f"An extension request could not be auto-approved ({needs_human}). Details:")

    # Case (5): Student's status (and, if applicable, partner's status) are "clean" - and the extension as a whole
    # qualifies for an auto-extension! So we can go ahead and process the extension for the student and the partner.
    else:

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

        student.set_status_approved()
        student.dispatch_writes()
        send_email(student)

        if partner:
            partner.set_status_approved()
            partner.dispatch_writes()
            send_email(partner)

        slack.send_student_update("An extension request was automatically approved!", autoapprove=True)
