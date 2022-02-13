from datetime import datetime, timedelta

from src.gradescope import Gradescope


class TestGradescope:
    def test_apply_extension_success(self):
        # If a new_hard_due_date is not provided, we bump BOTH the due date and the late due date, just in case
        # the class's late due dates are set to ~1hr after the due date, or something like that.
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
        )
        assert len(warnings) == 0

    def test_apply_extension_late_due_date_after_due_date(self):
        # In this case, the new hard due date is BEAFFORE the provided late due date, so we should apply the extension
        # normally.
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
            new_hard_due_date=datetime.now() + timedelta(5),
        )
        assert len(warnings) == 0

    def test_apply_extension_late_due_date_before_due_date(self):
        # In this case, the new due date is AFTER the provided late due date, so we should
        # throw a warning, but apply the extension up until the provided hard due date only.
        warnings = Gradescope().apply_extension(
            assignment_urls=["https://www.gradescope.com/courses/56746/assignments/942482/review_grades"],
            email="shomil+cs161test@berkeley.edu",
            new_due_date=datetime.now() + timedelta(3),
            new_hard_due_date=datetime.now() - timedelta(3),
        )
        assert len(warnings) == 1

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
