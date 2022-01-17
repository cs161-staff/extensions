import os
from src.record import StudentRecord
from src.submission import FormSubmission

from src.errors import SlackError
from src.utils import Environment


class SlackManager:
    """
    A container to hold Slack-related utilities.
    """

    def __init__(self) -> None:
        self.endpoint = Environment.get_variable("SLACK_ENDPOINT")

    def set_current_student(self, submission: FormSubmission, student: StudentRecord):
        self.submission = submission
        self.student = student

    def send_student_update(self, message: str) -> None:
        print(message)
        print(self.submission)
        print(self.student)
        pass

    def send_error(self, error: str) -> None:
        print(error)
        pass
