from __future__ import annotations
import datetime
from typing import List
from src.errors import EmailError
from sendgrid.helpers.mail import Cc

from src.utils import Environment
from src.record import StudentRecord
from src.assignments import AssignmentManager
from dateutil import parser
from markdown2 import Markdown
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class Email:
    """
    A class that enables creating, previewing, and sending emails. Email configuration data is stored in
    environment variables (this class is currently set up to use the Sendgrid mail relay system.)
    """

    def __init__(
        self,
        to_emails: List[str],
        from_email: List[str],
        cc_emails: List[str],
        reply_to: str,
        subject: str,
        body: str,
    ) -> None:
        self.to_emails = to_emails
        self.from_email = from_email
        self.cc_emails = cc_emails
        self.reply_to = reply_to
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

                body += f"**{name}**" + "<br>"
                body += f"*Original Deadline:* {fmt_date(original)}" + "<br>"
                body += f"*Extended Deadline:* {fmt_date(extended)}" + "<br>"
                body += f"*Num Days Extended:* {num_days} days" + "<br>"
                body += "\n\n"

        body += "\n"
        comments = student.get_email_comments()
        if comments:
            body += f"Additional comments: *{comments}*" + "\n\n"

        body += "If something doesn't look right, please reply to this email!"
        body += "\n\n"
        body += "Best,"
        body += "\n\n"
        body += Environment.get("EMAIL_SIGNATURE")

        return Email(
            to_emails=[student.get_email()],
            from_email=Environment.get("EMAIL_FROM"),
            cc_emails=[e.strip() for e in Environment.get("EMAIL_CC").split(",")],
            reply_to=Environment.get("EMAIL_REPLY_TO"),
            subject=Environment.get("EMAIL_SUBJECT"),
            body=body,
        )

    def preview(self) -> None:
        print("To:", self.to_emails)
        print("From:", self.from_email)
        print("CC:", self.cc_emails)
        print("Reply-to:", self.reply_to)
        print("Subject:", self.subject)
        print("Body:")
        print(self.body)

    def send(self) -> None:
        html_body = Markdown().convert(self.body)
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_emails,
            subject=self.subject,
            html_content=html_body,
        )
        if self.cc_emails:
            message.add_cc([Cc(e, e) for e in self.cc_emails])
        if self.reply_to:
            message.reply_to = self.reply_to

        try:
            sg = SendGridAPIClient(Environment.get("SENDGRID_API_KEY"))
            sg.send(message)
        except Exception as e:
            print(message)
            print(e.body)
            raise EmailError("An error occurred while sending an email:", e.body)
