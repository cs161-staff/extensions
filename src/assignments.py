from datetime import datetime
from typing import List, Optional

from dateutil import parser
from pytz import timezone

from src.errors import ConfigurationError
from src.sheets import Sheet
from src.utils import cast_bool, cast_date, cast_list_str

PST = timezone("US/Pacific")


class Assignment:
    """
    An instance of an assignment, created from a user-provided list of assignments.
    """

    def __init__(
        self,
        name: str,
        id: str,
        due_date: Optional[datetime],
        hard_due_date: Optional[datetime],
        partner: bool,
        gradescope: List[str],
    ) -> None:
        self.name = name
        self.id = id
        self.due_date = due_date
        self.hard_due_date = hard_due_date
        self.partner = partner
        self.gradescope = gradescope

    def is_past_due(self, request_time: str):
        """
        Return true if this extension request was submitted after an assignment was due.
        """
        # Encoding default behavior: if the due date is not set, then this assignment is NOT past due.
        # Thus, a request may qualify for auto-approval even if the due date is not set!
        if not self.due_date:
            return False

        request_time: datetime = parser.parse(request_time)
        if request_time.tzinfo is None:
            request_time = PST.localize(request_time)
        if request_time > self.due_date:
            return True
        else:
            return False

    def get_name(self) -> str:
        return self.name

    def get_id(self) -> str:
        return self.id

    def get_due_date(self) -> Optional[datetime]:
        return self.due_date

    def get_hard_due_date(self) -> Optional[datetime]:
        return self.hard_due_date

    def is_partner_assignment(self):
        return self.partner

    def get_gradescope_assignment_urls(self) -> List[str]:
        return self.gradescope


class AssignmentList:
    """
    A list of assignments, created from the user-provided "Assignments" sheet. Supports assignment lookup by name/id.
    """

    def __init__(self, sheet: Sheet) -> None:
        assignments: List[Assignment] = []
        for row in sheet.get_all_records():
            name = row["name"]
            if name:
                assignments.append(
                    Assignment(
                        name=name,
                        id=row["id"],
                        due_date=cast_date(row.get("due_date", ""), optional=True),
                        hard_due_date=cast_date(row.get("hard_due_date", ""), optional=True),
                        partner=cast_bool(row["partner"]),
                        gradescope=cast_list_str(row.get("gradescope", "")),
                    )
                )

        self.assignments = assignments

    def __iter__(self):
        for a in self.assignments:
            yield a

    def get_all_ids(self) -> List[str]:
        return [a.id for a in self.assignments]

    def from_id(self, id: str) -> Assignment:
        for assignment in self.assignments:
            if assignment.id == id:
                return assignment
        raise ConfigurationError(f"Assignment with ID {id} not found.")

    def from_name(self, name: str) -> Assignment:
        for assignment in self.assignments:
            if assignment.name == name:
                return assignment
        raise ConfigurationError(f"Assignment with name {name} not found.")
