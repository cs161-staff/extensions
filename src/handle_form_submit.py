from src.assignments import AssignmentList
from src.email import Email
from src.errors import ConfigurationError, KnownError
from src.gradescope import Gradescope
from src.record import StudentRecord
from src.sheets import (
    SHEET_ASSIGNMENTS,
    SHEET_ENVIRONMENT_VARIABLES,
    SHEET_FORM_QUESTIONS,
    SHEET_STUDENT_RECORDS,
    BaseSpreadsheet,
)
from src.slack import SlackManager
from src.submission import FormSubmission
from src.utils import Environment

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
    assignments = AssignmentList(sheet=sheet_assignments)

    # Fetch form submission.
    submission = FormSubmission(form_payload=request_json["form_data"], question_sheet=sheet_form_questions)

    # Extract this student's record (throws if email does not exist)
    student = StudentRecord.from_email(email=submission.get_email(), sheet_records=sheet_records)

    # Get a pointer to Slack, and set the current student
    slack = SlackManager()
    slack.set_current_student(submission=submission, student=student, assignments=assignments)

    # -----------------------------------------------------------------------------------------------------------------
    # Section 1: The student submitted a general plea for help.
    # -----------------------------------------------------------------------------------------------------------------
    if not submission.knows_assignments():
        print("Student requested general extension without specific assignments...")
        student.set_status_requested_meeting()
        student.flush()
        slack.send_student_update("A student requested a student support meeting.")
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
        print("Attempting to look up partner by email.")
        partner = StudentRecord.from_email(email=submission.get_partner_email(), sheet_records=sheet_records)

    num_requests = len(submission.get_requests(assignments=assignments))

    for assignment_id, num_days in submission.get_requests(assignments=assignments).items():
        print(f"[{assignment_id}] Processing request for {num_days} days.")
        assignment = assignments.from_id(assignment_id)

        # If student requests new extension that's shorter than previously requested extension, then treat this request
        # as the previously requested extension (this helps us with the case where Partner A requests 8 day ext. and B
        # requests 3 day ext.) In all other cases (e.g. if new request is longer than old one), we treat it as a normal
        # request and overwrite the existing record.
        existing_request = student.get_assignment(assignment_id=assignment_id)
        if existing_request and num_days <= existing_request:
            slack.add_warning(
                f"[{assignment_id}] Student requested an extension for {num_days} days, which was <= an existing request of {existing_request} days, so we kept the existing request in-place."
            )
            num_days = existing_request

        # Flag Case #1: The number of requested days is too large (non-DSP).
        if not submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold():
            if Environment.get_auto_approve_threshold() <= 0:
                needs_human = f"auto-approve is disabled"
            else:
                needs_human = f"a request of {num_days} days is greater than auto-approve threshold of {Environment.get_auto_approve_threshold()} days"

        # Flag Case #2: The number of requested days is too large (DSP).
        elif submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold_dsp():
            needs_human = f"a DSP request of {num_days} days is greater than DSP auto-approve threshold"

        # Flag Case #3: The student has requested extensions on too many assignments in a single submission
        elif not submission.claims_dsp() and num_requests > Environment.get_auto_approve_assignment_threshold():
            needs_human = f"this student has requested more assignment extensions ({num_requests}) than the auto-approve threshold ({Environment.get_auto_approve_assignment_threshold()})"

        # Flag Case #4: This extension request is retroactive (the due date is in the past)
        elif assignment.is_past_due(request_time=submission.get_timestamp()):
            needs_human = "this student requested a retroactive extension on an assignment"

        # Passed all cases, so proceed.
        else:
            print(f"[{assignment_id}] request meets criteria for auto-approval")

        # Regardless of whether or not this needs a human, we write the number of days requested back onto the
        # roster sheet (this is in a queue-style format, where we queue up these writes and then batch-process
        # them all at the end).
        student.queue_write_back(col_key=assignment_id, col_value=num_days)

        # We do the same for the partner, if this assignment has a partner and the submission has a partner.
        if assignment.is_partner_assignment() and submission.has_partner():
            partner.queue_write_back(col_key=assignment_id, col_value=num_days)

        # Aside: if the form submission claims DSP, but the student record isn't marked as DSP, then flag it
        if submission.claims_dsp() and not student.is_dsp():
            slack.add_warning(
                f"Student {submission.get_email()} responded '{submission.dsp_status()}' to "
                + "DSP question in extension request, but is not marked for DSP approval on the roster. "
                + "Please investigate!"
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
        student.flush()
        partner.set_status_pending()
        partner.flush()
        slack.send_student_update(
            "An extension request needs review (there is work-in-progress for this student's record)."
        )

    # Case (2): Submission contains partner, and partner's status is a "work-in-progress"
    # We can't auto-approve here for either party (we're blocked on the partner).
    elif submission.has_partner() and partner.has_wip_status():
        partner.flush()
        student.set_status_pending()
        student.flush()

        slack.send_student_update(
            "An extension request needs review (there is work-in-progress for this student's partner)."
        )

    # Case (3): Submission doesn't contain partner, and student's status is a "work-in-progress"
    # Here, we don't want to touch the student's status (e.g. if it's "Meeting Requested", we want to leave
    # it as such). But we do want to update the roster with the number of days requested, so we dispatch writes.
    elif student.has_wip_status():
        student.flush()
        slack.send_student_update("An extension request needs review (there is work in progress for this student).")

    # Case (4): Student's status (and, if applicable, partner's status) are "clean" - there is no pending
    # activity in either of these rows, so we can go ahead and check if the extension as a whole qualifies
    # for auto-approval. In this case, it doesn't -- it needs a human!
    elif needs_human:
        student.set_status_pending()
        student.flush()

        if partner:
            partner.set_status_pending()
            partner.flush()

        slack.send_student_update(f"An extension request needs review ({needs_human}).")

    # Case (5): Student's status (and, if applicable, partner's status) are "clean" - and the extension as a whole
    # qualifies for an auto-extension! So we can go ahead and process the extension for the student and the partner.
    else:

        def send_email(user: StudentRecord):
            # Guard around the outbound email, so we can diagnose errors easily and keep state consistent.
            try:
                email = Email.from_student_record(student=user, assignments=assignments)
                email.send()
            except Exception as err:
                raise KnownError(
                    "Writes to spreadsheet succeed, but email to student failed.\n"
                    + "Please follow up with this student manually and/or check email logs.\n"
                    + "Error: "
                    + str(err)
                )

        student.set_status_approved()
        student.flush()

        if partner:
            partner.set_status_approved()
            partner.flush()
            slack.send_student_update(
                "An extension request was automatically approved (for a partner, too)!", autoapprove=True
            )

        else:
            slack.send_student_update("An extension request was automatically approved!", autoapprove=True)

        send_email(student)
        if partner:
            send_email(partner)

        if Gradescope.extend_gradescope_assignments_enabled():
            client = Gradescope()
            student.apply_gradescope_extensions(assignments=assignments, gradescope=client)
            if partner:
                partner.apply_gradescope_extensions(assignments=assignments, gradescope=client)
