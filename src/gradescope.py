from typing import List

from gradescope_api.client import GradescopeClient

from src.errors import GradescopeError
from src.utils import Environment, cast_bool, truncate


class Gradescope:
    """
    An interface to apply extensions to Gradescope. This relies on `cs161-staff/gradescope-api`, an unofficial,
    minimal Gradescope API wrapper designed specifically for extension management.
    """

    def __init__(self) -> None:
        email = Environment.get("GRADESCOPE_EMAIL")
        password = Environment.get("GRADESCOPE_PASSWORD")

        try:
            self.client = GradescopeClient(email=email, password=password)
        except Exception as err:
            raise GradescopeError(f"Failed to sign into Gradescope: {err}")

    @staticmethod
    def is_enabled():
        return cast_bool(Environment.safe_get("EXTEND_GRADESCOPE_ASSIGNMENTS", "No"))

    def apply_extension(self, assignment_urls: List[str], email: str, num_days: int) -> List[str]:
        warnings = []
        for assignment_url in assignment_urls:
            prefix = f"[{email}] [{assignment_url}] [{num_days}] "
            print("Extending: " + prefix)
            try:
                course = self.client.get_course(course_url=assignment_url)
                assignment = course.get_assignment(assignment_url=assignment_url)
                assignment.apply_extension(email=email, num_days=num_days)
            except Exception as err:
                print("GradescopeAPIError: " + str(err))
                warnings.append(
                    prefix
                    + f"failed to extend assignment in Gradescope: internal Gradescope error occurred ({truncate(err)})"
                )
        return warnings
