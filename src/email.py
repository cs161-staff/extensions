from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List

from sicp.common.rpc.mail import send_email

from src.assignments import AssignmentList
from src.errors import EmailError, KnownError
from src.record import StudentRecord
from src.utils import Environment, cast_list_str

ENV_EMAIL_FROM = "EMAIL_FROM"
ENV_EMAIL_REPLY_TO = "EMAIL_REPLY_TO"
ENV_EMAIL_SUBJECT = "EMAIL_SUBJECT"
ENV_EMAIL_SIGNATURE = "EMAIL_SIGNATURE"
ENV_EMAIL_CC = "EMAIL_CC"
ENV_APP_MASTER_SECRET = "APP_MASTER_SECRET"


class Email:
    """
    An interface for generating and sending templated emails via a preferred client (e.g. CS 162 Mailserver, SendGrid,
    Mailgun, etc.) - this is designed as an interface in case we need to switch away from CS 162's infra at any point.
    """

    def __init__(
        self,
        to_email: str,
        from_email: List[str],
        reply_to_email: str,
        cc_emails: List[str],
        subject: str,
        body: str,
    ) -> None:
        self.to_email = to_email
        self.from_email = from_email
        self.reply_to_email = reply_to_email
        self.cc_emails = cc_emails
        self.subject = subject
        self.body = body

    @classmethod
    def from_student_record(cls, student: StudentRecord, assignments: AssignmentList):
        body = "Hi,"
        body += "\n\n"
        body += (
            "You recently requested an extension for an assignment. "
            + "We've processed this extension, and here are your updated due dates:"
        )
        body += "\n\n"

        def fmt_date(dt: datetime):
            return dt.strftime("%A, %B %-d")

        for assignment in assignments:
            num_days = student.get_request(assignment_id=assignment.get_id())
            if num_days:
                name = assignment.get_name()

                if assignment.get_due_date():
                    original = assignment.get_due_date()
                    extended = original + timedelta(days=int(num_days))

                    body += f"{name} ({num_days} Day Extension)" + "\n"
                    body += f"Original Deadline: {fmt_date(original)}" + "\n"
                    body += f"Extended Deadline: {fmt_date(extended)}" + "\n"
                    body += "\n"
                else:
                    body += f"{name} ({num_days} Day Extension)" + "\n"
                    body += "Original Deadline: TBD" + "\n"
                    body += "Extended Deadline: TBD" + "\n"
                    body += "\n"

        comments = student.get_email_comments()
        if comments:
            body += f"Additional comments: {comments}" + "\n\n"

        body += "If something doesn't look right, please reply to this email!"
        body += "\n\n"
        body += "Best,"
        body += "\n\n"
        body += Environment.get(ENV_EMAIL_SIGNATURE)
        body += "\n\n"
        body += (
            "Disclaimer: This is an auto-generated email. We may follow up with you in"
            + " this thread, and feel free to reply to this thread if you'd like to follow up with us!"
        )

        cc_emails = cast_list_str(Environment.safe_get(ENV_EMAIL_CC, ""))

        return cls(
            to_email=student.get_email(),
            from_email=Environment.get(ENV_EMAIL_FROM),
            cc_emails=cc_emails,
            reply_to_email=Environment.get(ENV_EMAIL_REPLY_TO),
            subject=Environment.get(ENV_EMAIL_SUBJECT),
            body=body,
        )

    def send(self) -> None:
        # TODO: When 162 adds HTML support, bring back HTML emails.
        # html_body = Markdown().convert(self.body)
        # extra_headers = [("Content-Type", "text/html; charset=UTF-8")]
        extra_headers = [("Reply-To", self.reply_to_email)]
        if self.cc_emails:
            header = ("Cc", ", ".join(self.cc_emails))
            extra_headers.append(header)

        if not os.environ.get(ENV_APP_MASTER_SECRET):
            raise KnownError(
                "Internal error: environment master secret not set, so cannot send emails via the CS 162 mailserver!"
            )
        try:
            send_email(
                sender=Environment.get(ENV_EMAIL_FROM),
                target=self.to_email,
                targets=self.cc_emails,
                subject=self.subject,
                body=self.body,
                _impersonate="mail",
                extra_headers=extra_headers,
            )

        except Exception as e:
            raise EmailError("An error occurred while sending an email:", e)
