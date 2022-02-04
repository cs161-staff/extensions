from email.mime import base
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

from tests.MockSheet import MockSheet

DEV_URL = "https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit#gid=1214799044"


class TestIntegration:
    @classmethod
    def setup_class(cls):
        ss = gspread.service_account("service-account.json").open_by_url(DEV_URL)
        roster = ss.worksheet("Roster")
        headers = roster.get_all_values()[0]
        roster.clear()
        roster.update_cells([gspread.Cell(row=1, col=i + 1, value=header) for i, header in enumerate(headers)])

        base = BaseSpreadsheet(spreadsheet_url=DEV_URL)
        cls.sheet_assignments = MockSheet.from_live(base.get_sheet(SHEET_ASSIGNMENTS).sheet)
        cls.sheet_form_questions = MockSheet.from_live(base.get_sheet(SHEET_FORM_QUESTIONS).sheet)
        cls.sheet_env_vars = MockSheet.from_live(base.get_sheet(SHEET_ENVIRONMENT_VARIABLES).sheet)
        cls.sheet_records = MockSheet.from_live(base.get_sheet(SHEET_STUDENT_RECORDS).sheet)

    @classmethod
    def teardown_class(cls):
        cls.sheet_records.flush()

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
        slack = SlackManager()
        policy = Policy(
            sheet_assignments=TestIntegration.sheet_assignments,
            sheet_form_questions=TestIntegration.sheet_form_questions,
            sheet_env_vars=TestIntegration.sheet_env_vars,
            form_payload={"Timestamp": [timestamp]},
            slack=slack,
        )
        for key, value in mock_request.items():
            policy.submission.responses[key] = value
        policy.fetch_student_records(sheet_records=TestIntegration.sheet_records)
        return policy

    #########################################################################################################
    # AUTO APPROVALS: The following rows should all be auto-approved.
    #########################################################################################################
    def test_auto_approve_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="A1@berkeley.edu", assignments="Homework 1", days="1"),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="A2@berkeley.edu", assignments="Homework 1, Homework 2", days="2"),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_single_student_multiple_assignments_with_partner(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A3@berkeley.edu",
                assignments="Homework 1, Homework 2, Project 1 Checkpoint",
                days="3, 3, 3",
                has_partner="Yes",
                partner_email="A4@berkeley.edu",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_dsp_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="A5@berkeley.edu", assignments="Homework 1", days="6", is_dsp="Yes"),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_dsp_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A6@berkeley.edu", assignments="Homework 1, Homework 2", days="3, 4", is_dsp="Yes"
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_auto_approve_dsp_other_status(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A7@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="3, 4",
                is_dsp="My DSP letter is pending.",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    #########################################################################################################
    # MANUAL APPROVALS: Retroactive extension requests.
    #########################################################################################################
    def test_retroactive_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="R1@berkeley.edu", assignments="Homework 1", days="1"),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    def test_retroactive_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(email="R2@berkeley.edu", assignments="Homework 1, Homework 2", days="2"),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        policy.apply(silent=True)

    #########################################################################################################
    # MANUAL APPROVALS: Request # days > allowed # days.
    #########################################################################################################

    #########################################################################################################
    # MANUAL APPROVALS: Work-in-progress for a student (or partner).
    #########################################################################################################
