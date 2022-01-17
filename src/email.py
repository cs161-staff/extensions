from __future__ import annotations
from typing import List


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
        self.from_emails = from_email
        self.cc_emails = cc_emails
        self.reply_to = reply_to
        self.subject = subject
        self.body = body

    @staticmethod
    def from_student_record() -> Email:
        # TODO: Move this to the StudentRecord class.
        pass
    
    def preview(self) -> None:
        print('To:', self.to_emails)
        print('From:', self.from_emails)
        print('CC:', self.cc_emails)
        print('Reply-to:', self.reply_to)
        print('Subject:', self.subject)
        print('Body:')
        print(self.body)

    def send(self) -> None:
        pass
