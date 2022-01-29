from __future__ import annotations
import datetime
from typing import List
from src.errors import EmailError

from src.utils import Environment
from src.record import StudentRecord
from src.assignments import AssignmentManager
from dateutil import parser

from sicp.common.rpc.mail import send_email


class Email:
    """
    A class that enables creating, previewing, and sending emails. Email configuration data is stored in
    environment variables (this class is currently set up to use the 162 mail relay system.)
    """

    def __init__(
        self,
        to_emails: List[str],
        from_email: List[str],
        cc_emails: List[str],
        subject: str,
        body: str,
    ) -> None:
        self.to_emails = to_emails
        self.from_email = from_email
        self.cc_emails = cc_emails
        self.subject = subject
        self.body = body

    @staticmethod
    def from_student_record(student: StudentRecord, assignment_manager: AssignmentManager) -> Email:
        body = f"Hi {student.get_name()},"
        body += "\n\n"
        body += (
            "You recently requested an extension for an assignment. "
            + "We've processed this extension, and here are your updated due dates:"
        )
        body += "\n\n"

        fmt_date = lambda dt: dt.strftime("%A, %B %-d")

        for assignment_id in assignment_manager.get_all_ids():
            num_days = student.get_assignment(assignment_id=assignment_id)
            if num_days:
                name = assignment_manager.id_to_name(assignment_id=assignment_id)

                original = parser.parse(assignment_manager.get_due_date(assignment_id=assignment_id))
                extended = original + datetime.timedelta(days=int(num_days))

                body += f"{name} ({num_days} Day Extension)" + "\n"
                body += f"Original Deadline: {fmt_date(original)}" + "\n"
                body += f"Extended Deadline: {fmt_date(extended)}" + "\n"
                body += "\n"

        comments = student.get_email_comments()
        if comments:
            body += f"Additional comments: {comments}" + "\n\n"

        body += "If something doesn't look right, please reply to this email!"
        body += "\n\n"
        body += "Best,"
        body += "\n\n"
        body += Environment.get("EMAIL_SIGNATURE")
        body += "\n\n"
        body += "Disclaimer: This is an auto-generated email. We (the human course staff) may follow up with you in this thread, and feel free to reply to this thread if you'd like to follow up with us!"

        cc_emails = [e.strip() for e in Environment.safe_get("EMAIL_CC", "").split(",")]
        return Email(
            to_emails=[student.get_email()],
            from_email=Environment.get("EMAIL_FROM"),
            cc_emails=cc_emails,
            subject=Environment.get("EMAIL_SUBJECT"),
            body=body,
        )

    def preview(self) -> None:
        print("To:", self.to_emails)
        print("From:", self.from_email)
        print("CC:", self.cc_emails)
        print("Subject:", self.subject)
        print("Body:")
        print(self.body)

    def send(self) -> None:
        # TODO: When 162 adds HTML support, bring back HTML emails.
        # html_body = Markdown().convert(self.body)
        # extra_headers = [("Content-Type", "text/html; charset=UTF-8")]
        extra_headers = []
        if self.cc_emails:
            extra_headers.append(("Cc", self.cc_emails))
        try:
            send_email(
                sender=Environment.get("EMAIL_FROM"),
                target=self.to_emails,
                subject=self.subject,
                body=self.body,
                _impersonate="mail",
                extra_headers=extra_headers,
            )
        except Exception as e:
            print(self.body)
            raise EmailError("An error occurred while sending an email:", e)
