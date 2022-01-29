from datetime import datetime
from typing import List
from src.errors import ConfigurationError
from src.sheets import Sheet

from datetime import datetime
from pytz import timezone
from dateutil import parser

PST = timezone("US/Pacific")


class AssignmentManager:
    def __init__(self, sheet: Sheet) -> None:
        records = sheet.get_all_records()
        self.records = records

    def is_partner_assignment(self, assignment_id: str) -> bool:
        for record in self.records:
            if record["id"] == assignment_id:
                return record["partner"] == "Yes"

        raise ConfigurationError(f"Assignment with ID {assignment_id} not found.")

    def name_to_id(self, name: str) -> str:
        """
        Convert from an assignment name (e.g. Homework 1) to ID (e.g. hw1).
        """
        for record in self.records:
            if record["name"] == name:
                return record["id"]
        raise ConfigurationError(f"Assignment with name {name} not found.")

    def id_to_name(self, assignment_id: str) -> str:
        """
        Convert from an assignment ID to name.
        """
        for record in self.records:
            if record["id"] == assignment_id:
                return record["name"]
        raise ConfigurationError(f"Assignment with ID {assignment_id} not found.")

    def get_all_ids(self) -> List[str]:
        return [record.get("id") for record in self.records]

    def get_due_date(self, assignment_id: str) -> str:
        for record in self.records:
            if record["id"] == assignment_id:
                return record["due_date"]
        raise ConfigurationError(f"Assignment with ID {assignment_id} not found.")

    def is_retroactive(self, assignment_id: str, request_time: str):
        """
        Return true if this extension request was submitted after an assignment was due.
        """
        request_time = parser.parse(request_time)
        due_date = self.get_due_date(assignment_id=assignment_id)
        due_time = PST.localize(parser.parse(due_date + " 11:59 PM"))
        print(f"Comparing request_time={request_time} to due_time={due_time}")
        if request_time > due_time:
            return True
        else:
            return False
