from datetime import datetime

import pytz
from gradescope_api.client import GradescopeClient
from gradescope_api.errors import GradescopeAPIError

from src.errors import GradescopeError
from src.utils import Environment, cast_bool


class Gradescope:
    def __init__(self) -> None:
        email = Environment.get("GRADESCOPE_EMAIL")
        password = Environment.get("GRADESCOPE_PASSWORD")

        try:
            self.client = GradescopeClient(email=email, password=password)
        except GradescopeAPIError as err:
            raise GradescopeError(f"Failed to sign into Gradescope: {err}")

    @staticmethod
    def extend_gradescope_assignments_enabled() -> bool:
        return cast_bool(Environment.safe_get("EXTEND_GRADESCOPE_ASSIGNMENTS", "No"))

    def apply_extension(self, assignment_url: str, email: str, new_due_date: datetime):
        course = self.client.get_course(course_url=assignment_url)
        student = course.get_student(email=email)
        assignment = course.get_assignment(assignment_url=assignment_url)
        new_due_date_utc = new_due_date.astimezone(pytz.utc)
        try:
            assignment.create_extension(user_id=student.get_user_id(), due_date=new_due_date_utc)
            print(f"Successfully extended deadline for {email} to {new_due_date} on assignment {assignment_url}")
        except GradescopeAPIError as err:
            raise GradescopeError(f"Failed to create Gradescope assignment extension: {err}")
