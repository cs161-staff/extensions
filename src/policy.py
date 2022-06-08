from typing import Any, Dict, List, Optional

from src.assignments import AssignmentList
from src.email import Email
from src.gradescope import Gradescope
from src.record import StudentRecord
from src.sheets import Sheet
from src.slack import SlackManager
from src.submission import FormSubmission
from src.utils import Environment


class Policy:
    def __init__(
        self,
        sheet_assignments: Sheet,
        sheet_form_questions: Sheet,
        form_payload: Dict[str, Any],
        slack: SlackManager,
    ):

        # Validate/extract assignments into model
        self.assignments = AssignmentList(sheet=sheet_assignments)

        # Validate/extract form submission into model
        self.submission = FormSubmission(
            form_payload=form_payload, question_sheet=sheet_form_questions, assignments=self.assignments
        )

        self.slack = slack

    def fetch_student_records(self, sheet_records: Sheet):
        # Validate/extract student (and partner, if applicable) records
        self.student = StudentRecord.from_email(email=self.submission.get_email(), sheet_records=sheet_records)
        self.partners: List[StudentRecord] = []
        if self.submission.has_partner():
            self.partners = [
                StudentRecord.from_email(email=email, sheet_records=sheet_records)
                for email in self.submission.get_partner_emails()
            ]

        # Set up a connection to Slack, so we can stream output there
        self.slack.set_current_student(submission=self.submission, student=self.student, assignments=self.assignments)

    def apply(self, silent: bool = False) -> bool:
        if silent:
            self.slack.suppress()

        reason = (
            self.submission.get_reason() if self.submission.knows_assignments() else self.submission.get_game_plan()
        )

        self.student.set_last_run_timestamp(timestamp=self.submission.get_timestamp())
        self.student.set_last_run_reason(reason=reason)
        if self.partners:
            for partner in self.partners:
                partner.set_last_run_timestamp(timestamp=self.submission.get_timestamp())
                partner.set_last_run_reason(reason=reason + f" [source: {self.submission.get_email()}]")

        # Step 1: If this is a request for a student support meeting, exit early.
        if not self.submission.knows_assignments():
            self.student.set_log("Requested student support meeting.")
            self.student.set_status_requested_meeting()
            self.slack.send_student_update("A student requested a student support meeting.")
            self.student.flush()
            return False

        # Step 2: Inspect the submission, and determine if it requires manual approval.
        # This step also pipes form submission data into the roster spreadsheet.
        needs_human = self.process_submission()
        if needs_human:
            self.slack.send_student_update(f"An extension request needs review ({needs_human}).")
            return False

        # Step 3: Check to see if there's any existing "work-in-progress" that might block auto-approval.
        # This makes sure we don't auto-approve rows that are marked as "Pending" already.
        work_in_progress = self.check_work_in_progress()
        if work_in_progress:
            self.slack.send_student_update(work_in_progress)
            return False

        # Step 4: Before we approve, add anything that we may want to bring to the reviewer's attention.
        # We add all warnings to the bottom of the Slack message.
        self.check_for_warnings()

        # Step 5: All checks have passed, so auto-approve the extension request!
        message = self.approve()

        # Step 6: Send the email.
        if not silent:
            self.send_email(target=self.student)
            if self.partners:
                for partner in self.partners:
                    self.send_email(target=partner)

        # TODO: Step 7: If enabled, extend deadlines on Gradescope.
        if not silent:
            self.extend_assignments(target=self.student)
            if self.partners:
                for partner in self.partners:
                    self.extend_assignments(target=partner)

        self.slack.send_student_update(message=message, autoapprove=True)

        return True

    def check_work_in_progress(self) -> Optional[str]:
        work_in_progress = None

        # Case (1): Submission contains partner, and student's status is a "work-in-progress".
        # We can't auto-approve here for either party (we're blocked on the student).
        if self.submission.has_partner() and self.student.has_wip_status():
            self.student.flush()
            for partner in self.partners:
                partner.set_status_pending()
                partner.set_log(f"Work-in-progress for form submitter [submitter: {self.student.get_email()}].")
                partner.flush()
            work_in_progress = (
                "An extension request needs review (there is work-in-progress for this student's record)."
            )

        # Case (2): Submission contains partner(s), and at least one partner's status is a "work-in-progress"
        # We can't auto-approve here for anyone (we're blocked on one or more partners).
        elif self.submission.has_partner() and any([partner.has_wip_status() for partner in self.partners]):

            # Dirty partners are partners with work-in-progress rows (e.g. we want to leave them as is).
            dirty_partners = [partner for partner in self.partners if partner.has_wip_status()]
            for partner in dirty_partners:
                partner.flush()

            # Construct a log message that describes what happened in this case.
            wip_emails = ", ".join([p.get_email() for p in dirty_partners])
            msg = (
                f"Work-in-progress for submitter's partner [submitter: {self.submission.get_email()}] "
                + f"[partner(s) with WIP: {wip_emails}]."
            )

            # Clean partners are partners with "clean" rows (e.g. we want to flip them to yellow).
            clean_partners = [partner for partner in self.partners if not partner.has_wip_status()]
            for partner in clean_partners:
                partner.set_status_pending()
                partner.set_log(msg)
                partner.flush()

            # We want to flip the student's row to yellow.
            self.student.set_status_pending()
            self.student.set_log(msg)
            self.student.flush()
            work_in_progress = (
                "An extension request needs review (there is work-in-progress for this student's partner)."
            )

        # Case (3): Submission doesn't contain partner, and student's status is a "work-in-progress"
        # Here, we don't want to touch the student's status (e.g. if it's "Meeting Requested", we want to leave
        # it as such). But we do want to update the roster with the number of days requested, so we dispatch writes.
        elif self.student.has_wip_status():
            self.student.flush()
            work_in_progress = (
                "An extension request needs review (there is work in progress for this student's record)."
            )

        return work_in_progress

    def process_submission(self) -> Optional[str]:
        needs_human = None

        # Check to see if the student requested a bunch of extensions all within this request.
        num_requests = self.submission.get_num_requests()
        if not self.submission.claims_dsp() and num_requests > Environment.get_auto_approve_assignment_threshold():
            needs_human = (
                f"this student has requested more assignment extensions ({num_requests}) than the "
                + f"auto-approve threshold ({Environment.get_auto_approve_assignment_threshold()})"
            )

        total_num_extensions = self.student.count_requests(assignments=self.assignments) + num_requests

        # Walk through each extension request contained within this form submission.
        for assignment, num_days in self.submission.get_requests():

            # If student requests new extension that's shorter than previously requested extension, then treat this
            # request as the previously requested extension (this helps us with the case where Partner A requests 8
            # day ext. and B requests 3 day ext.) In all other cases (e.g. if new request is longer than old one), we
            # treat it as a normal request and overwrite the existing record.
            existing_request = self.student.get_request(assignment_id=assignment.get_id())
            if existing_request and num_days <= existing_request:
                self.slack.add_warning(
                    f"[{assignment.get_name()}] student requested an extension for {num_days} days, which "
                    + f"was <= an existing request of {existing_request} days, so we kept the existing request in-place."
                )
                num_days = existing_request

            # Flag Case #1: The number of requested days is too large (non-DSP).
            if not self.submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold():
                if Environment.get_auto_approve_threshold() <= 0:
                    needs_human = "auto-approve is disabled"
                else:
                    needs_human = (
                        f"a request of {num_days} days is greater than auto-approve threshold "
                        + f"of {Environment.get_auto_approve_threshold()} days"
                    )

            # Flag Case #2: The number of requested days is too large (DSP).
            elif self.submission.claims_dsp() and num_days > Environment.get_auto_approve_threshold_dsp():
                needs_human = f"a DSP request of {num_days} days is greater than DSP auto-approve threshold"

            # Flag Case #3: This extension request is retroactive (the due date is in the past).
            elif assignment.is_past_due(request_time=self.submission.get_timestamp()):
                needs_human = "student requested a retroactive extension on an assignment"

            # Flag Case #4: The student has requested an extension on too many assignments (non-DSP).
            elif (
                not self.submission.claims_dsp()
                and Environment.get_max_total_requested_extensions_threshold() != -1
                and total_num_extensions > Environment.get_max_total_requested_extensions_threshold()
            ):
                needs_human = (
                    f"a student requested extensions on more assignments ({total_num_extensions} total)"
                    + " than the designated threshold"
                )
                print(needs_human)

            print(Environment.get_max_total_requested_extensions_threshold(), total_num_extensions)

            # Regardless of whether or not this needs a human, we write the number of days requested back onto the
            # roster sheet. Note that this write isn't pushed until we call flush().
            self.student.queue_write_back(col_key=assignment.get_id(), col_value=num_days)

            # We do the same for the partner, if this assignment has a partner and the submission has a partner.
            if assignment.is_partner_assignment() and self.partners:
                for partner in self.partners:
                    partner.queue_write_back(col_key=assignment.get_id(), col_value=num_days)

        # If this request needs a human, we update statuses to "pending" and proceed.
        if needs_human:
            self.student.set_status_pending()
            self.student.set_log(
                f"{needs_human.capitalize()} [submitter: {self.student.get_email()}]"
                if self.partners
                else needs_human.capitalize()
            )
            self.student.flush()
            if self.partners:
                for partner in self.partners:
                    partner.set_status_pending()
                    partner.set_log(f"{needs_human.capitalize()} [submitter: {self.student.get_email()}]")
                    partner.flush()

        return needs_human

    def check_for_warnings(self):
        if self.submission.claims_dsp() and (self.student.roster_contains_dsp_status() and not self.student.is_dsp()):
            self.slack.add_warning(
                f"Student {self.submission.get_email()} responded '{self.submission.dsp_status()}' to "
                + "DSP question in extension request, but is not marked for DSP approval on the roster. "
                + "Please investigate!"
            )

    def approve(self):
        self.student.set_status_approved()
        self.student.set_log("Auto-approved.")
        self.student.flush()

        if not self.partners:
            message = "An extension request was automatically approved!"
        else:
            for partner in self.partners:
                partner.set_status_approved()
                partner.set_log(f"Auto-approved [request source: {self.student.get_email()}].")
                partner.flush()
            message = "An extension request was automatically approved (for the submitter's partner(s), too!)"

        return message

    def send_email(self, target: StudentRecord):
        try:
            email = Email.from_student_record(student=target, assignments=self.assignments)
            email.send()
        except Exception as err:
            print(err)
            self.slack.add_warning(
                "Writes to spreadsheet succeed, but email to student failed.\n"
                + "Please follow up with this student manually and/or check email logs.\n"
                + "Error: "
                + str(err)
            )

    def extend_assignments(self, target: StudentRecord):
        if Gradescope.is_enabled():
            client = Gradescope()
            warnings = target.apply_extensions(assignments=self.assignments, gradescope=client)
            for warning in warnings:
                self.slack.add_warning(warning)
