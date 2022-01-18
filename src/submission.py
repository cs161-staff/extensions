from typing import Any, Dict, List
from urllib import request
from xmlrpc.client import Boolean
from src.assignments import AssignmentManager
from src.errors import ConfigurationError, FormInputError

from src.sheets import Sheet


class FormSubmission:
    """
    A container to hold, manage, and format student form submissions (extension requests).
    """

    def __init__(self, form_payload: Dict[str, Any], question_sheet: Sheet) -> None:
        """
        Initializes a FormSubmission object to process a student's form submissions. We use an intermediary
        "Form Questions" spreadsheet to allow us to rename form questions without impacting the underlying
        data pointers.
        """
        print(form_payload)

        self.responses = {}
        
        for row in question_sheet.get_all_records():
            question = row.get("question")
            if not question:
                raise ConfigurationError("The Form Question sheet is missing a 'question' column.")
            key = row.get("key")
            if not key:
                raise ConfigurationError(f"The Form Question sheet is missing a key for question: {question}")
            if question in form_payload:
                self.responses[key] = str(form_payload[question][0])

        print(self.responses)

    def get_sid(self) -> str:
        return str(self.responses["sid"])

    def get_email(self) -> str:
        return str(self.responses["email"])

    def is_dsp(self) -> bool:
        return self.responses["is_dsp"] == "Yes"

    def knows_assignments(self) -> bool:
        return self.responses["knows_assignments"] == "Yes"

    def get_raw_requests(self) -> str:
        return self.responses['assignments']

    def get_raw_days(self) -> str:
        return self.responses['days']

    def get_requests(self, assignment_manager: AssignmentManager) -> Dict[str, Any]:
        """
        Fetch a map of ID to # days requested.
        """
        try:
            clean = lambda arr: [str(x).strip() for x in arr]
            names = clean(self.responses["assignments"].split(","))
            days = clean(str(self.responses["days"]).split(","))

            if len(names) != len(days):
                raise FormInputError("# assignment names provided does not equal # days requested for each assignment.")

            requests = {}
            for name, days in zip(names, days):
                assignment_id = assignment_manager.name_to_id(name)
                num_days = int(days)
                requests[assignment_id] = num_days

            return requests

        except Exception as e:
            raise FormInputError(
                "An error occurred while processing this student's form submission.\n"
                + f"Submission: {self.responses}\n"
                + f"Error: {e}"
            )

    def get_reason(self) -> str:
        return self.responses["reason"]

    def has_partner(self) -> bool:
        return self.responses["has_partner"] == "Yes"

    def get_partner_sid(self) -> str:
        return self.responses["partner_sid"]

    def get_partner_email(self) -> str:
        return self.responses["partner_email"]

    def get_game_plan(self) -> str:
        return self.responses["game_plan"]
