from typing import Any, Dict

import gspread
from src.policy import Policy
from src.sheets import (
    SHEET_ASSIGNMENTS,
    SHEET_ENVIRONMENT_VARIABLES,
    SHEET_FORM_QUESTIONS,
    SHEET_STUDENT_RECORDS,
    BaseSpreadsheet,
)
from src.slack import SlackManager
from src.utils import Environment

DEV_URL = "https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit#gid=1214799044"


class TestIntegration:
    @classmethod
    def setup_class(cls):
        ss = gspread.service_account("service-account.json").open_by_url(DEV_URL)
        roster = ss.worksheet("Roster")
        headers = roster.get_all_values()[0]
        roster.clear()
        roster.update_cells([gspread.Cell(row=1, col=i + 1, value=header) for i, header in enumerate(headers)])

    def get_request(
        self,
        email: str,
        days: str,
        assignments: str,
        is_dsp: str = "No",
        reason: str = "Test reason.",
        has_partner: str = "No",
        partner_email: str = "",
    ):
        return {
            "sid": "123456",
            "email": email,
            "is_dsp": is_dsp,
            "knows_assignments": "Yes",
            "assignments": assignments,
            "days": days,
            "reason": reason,
            "has_partner": has_partner,
            "partner_email": partner_email,
            "partner_sid": "123456",
            "game_plan": "",
            "ignore": "",
        }

    def get_policy(self, mock_request: Dict[str, Any], timestamp: str):
        base = BaseSpreadsheet(spreadsheet_url=DEV_URL)
        slack = SlackManager()
        policy = Policy(
            sheet_assignments=base.get_sheet(SHEET_ASSIGNMENTS),
            sheet_form_questions=base.get_sheet(SHEET_FORM_QUESTIONS),
            sheet_env_vars=base.get_sheet(SHEET_ENVIRONMENT_VARIABLES),
            form_payload={"Timestamp": [timestamp]},
            slack=slack,
        )
        for key, value in mock_request.items():
            policy.submission.responses[key] = value
        policy.fetch_student_records(sheet_records=base.get_sheet(SHEET_STUDENT_RECORDS))
        return policy

    def test_auto_approve_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="1@berkeley.edu", assignments="Homework 1", days="1"),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_retroactive_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="2@berkeley.edu", assignments="Homework 1", days="1"),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="3@berkeley.edu", assignments="Homework 1, Homework 2", days="2"),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_retroactive_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="4@berkeley.edu", assignments="Homework 1, Homework 2", days="2"),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)
