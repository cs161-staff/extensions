from datetime import datetime, timedelta

from src.gradescope import Gradescope


class TestGradescope:
    def test_apply_extension_success(self):
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
        assert len(warnings) == 0

    def test_apply_extension_invalid_url(self):
        # Try to apply an extension to an invalid URL
        warnings = Gradescope().apply_extension(
            assignment_urls=["hello world"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
        assert len(warnings) > 0

    def test_apply_extension_missing_permissions(self):
        # Try to apply an extension for an assignment that this user doesn't have access to
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/225521/assignments/929761/submissions/77765968"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
        assert len(warnings) > 0

    def test_apply_extension_invalid_student(self):
        # Try to apply an extension for an assignment with an invalid student
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="helloworld@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
        assert len(warnings) > 0
