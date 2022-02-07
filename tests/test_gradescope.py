from datetime import datetime, timedelta

from src.gradescope import Gradescope


class TestGradescope:
    def test_apply_extension(self):
        gradescope = Gradescope()
        gradescope.apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
