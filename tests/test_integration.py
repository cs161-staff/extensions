from typing import Any, Dict

import gspread
import pytest
from src.assignments import AssignmentList
from src.errors import KnownError
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
        Environment.configure_env_vars(TestIntegration.sheet_env_vars)
        slack = SlackManager()
        policy = Policy(
            sheet_assignments=TestIntegration.sheet_assignments,
            sheet_form_questions=TestIntegration.sheet_form_questions,
            form_payload={"Timestamp": [timestamp]},
            slack=slack,
        )
        for key, value in mock_request.items():
            policy.submission.responses[key] = value
        policy.fetch_student_records(sheet_records=TestIntegration.sheet_records)
        return policy

    #########################################################################################################
    # [Z] REQUESTED MEETING: Try a "Requested Meeting" request
    #########################################################################################################
    def test_requested_meeting(self):
        policy = self.get_policy(
            mock_request={
                "sid": "123456",
                "email": "Z1@berkeley.edu",
                "knows_assignments": "No",
                "has_partner": "",
                "game_plan": "test_requested_meeting",
                "ignore": "",
            },
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_requested_meeting_existing_work(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="Z2@berkeley.edu",
                assignments="Homework 1",
                days="1",
                reason="test_requested_meeting_existing_work",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

        policy = self.get_policy(
            mock_request={
                "sid": "123456",
                "email": "Z2@berkeley.edu",
                "knows_assignments": "No",
                "has_partner": "",
                "game_plan": "test_requested_meeting_existing_work",
                "ignore": "",
            },
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    #########################################################################################################
    # [A] AUTO APPROVALS: The following rows should all be auto-approved.
    #########################################################################################################
    def test_auto_approve_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A1@berkeley.edu",
                assignments="Homework 1",
                days="1",
                reason="test_auto_approve_single_student_single_assignment",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A2@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="2",
                reason="test_auto_approve_single_student_multiple_assignments",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_single_student_multiple_assignments_with_partner(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A3@berkeley.edu",
                assignments="Homework 1, Homework 2, Project 1 Checkpoint",
                days="3, 3, 3",
                has_partner="Yes",
                partner_email="A4@berkeley.edu",
                reason="test_auto_approve_single_student_multiple_assignments_with_partner",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_dsp_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A5@berkeley.edu",
                assignments="Homework 1",
                days="6",
                is_dsp="Yes",
                reason="test_auto_approve_dsp_single_assignment",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_dsp_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A6@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="3, 4",
                is_dsp="Yes",
                reason="test_auto_approve_dsp_multiple_assignments",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_dsp_other_status(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A7@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="3, 4",
                is_dsp="My DSP letter is pending.",
                reason="test_auto_approve_dsp_other_status",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_deadline_not_set(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A8@berkeley.edu",
                assignments="Project 3 (Code/Writeup)",
                days="3",
                reason="test_auto_approve_deadline_not_set",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert policy.apply(silent=True)

    def test_auto_approve_form_does_not_contain_has_partner_field(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="A9@berkeley.edu",
                assignments="Homework 1",
                days="1",
                reason="test_auto_approve_form_does_not_contain_has_partner_field",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        # delete the has_partner field entirely
        del policy.submission.responses["has_partner"]
        assert policy.apply(silent=True)

    #########################################################################################################
    # [B] MANUAL APPROVALS: Retroactive extension requests.
    #########################################################################################################
    def test_retroactive_single_student_single_assignment(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="B1@berkeley.edu",
                assignments="Homework 1",
                days="1",
                reason="test_retroactive_single_student_single_assignment",
            ),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_retroactive_single_student_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="B2@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="2",
                reason="test_retroactive_single_student_multiple_assignments",
            ),
            timestamp="2023-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    #########################################################################################################
    # [C] MANUAL APPROVALS: Request # days > allowed # days.
    #########################################################################################################
    def test_flag_request_too_many_days(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C1@berkeley.edu", assignments="Homework 1", days="10", reason="test_flag_request_too_many_days"
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_request_too_many_days_with_partner(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C1@berkeley.edu",
                assignments="Project 1 Checkpoint",
                days="10",
                has_partner="Yes",
                partner_email="C1.5@berkeley.edu",
                reason="test_flag_request_too_many_days_with_partner",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_request_too_many_days_dsp(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C2@berkeley.edu",
                assignments="Homework 1",
                days="10",
                is_dsp="Yes",
                reason="test_flag_request_too_many_days_dsp",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_request_too_many_days_multiple_assignments(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C3@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="10, 2",
                reason="test_flag_request_too_many_days_multiple_assignments",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_too_many_submissions_in_one_request(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C4@berkeley.edu",
                assignments="Homework 1, Homework 2, Homework 3, Homework 4, Homework 5, Homework 6",
                days="10",
                reason="test_flag_too_many_submissions_in_one_request",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_too_many_total_submissions_non_dsp(self):
        # Note: based on environment variables, the threshold for # of assignments allowed is 6.
        for i in range(1, 7):
            policy = self.get_policy(
                mock_request=self.get_request(
                    email="C4.5@berkeley.edu",
                    assignments=f"Homework {i}",
                    days="2",
                    reason="test_flag_too_many_submissions",
                ),
                timestamp="2022-01-27T20:46:42.125Z",
            )
            assert policy.apply(silent=True)

        # The 7th request should trigger manual approval.
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C4.5@berkeley.edu",
                assignments="Homework 7",
                days="2",
                reason="test_flag_too_many_submissions",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_request_too_many_days_with_multiple_partners(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="C5@berkeley.edu",
                assignments="Project 1 Checkpoint",
                days="10",
                has_partner="Yes",
                partner_email="C5.5@berkeley.edu, C5.6@berkeley.edu, C5.7@berkeley.edu",
                reason="test_flag_request_too_many_days_with_multiple_partners",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    #########################################################################################################
    # [D] MANUAL APPROVALS: Work-in-progress for a student (or partner).
    #########################################################################################################
    def test_flag_wip_for_student(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="D1@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="4,4",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

        policy = self.get_policy(
            mock_request=self.get_request(
                email="D1@berkeley.edu", assignments="Homework 3", days="2", reason="test_flag_wip_for_student"
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_wip_for_partner(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="D2@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="4,4",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

        policy = self.get_policy(
            mock_request=self.get_request(
                email="D3@berkeley.edu",
                assignments="Project 1 Checkpoint",
                days="2",
                has_partner="Yes",
                partner_email="D2@berkeley.edu",
                reason="test_flag_wip_for_partner",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    def test_flag_wip_for_student_with_partner(self):
        policy = self.get_policy(
            mock_request=self.get_request(
                email="D4@berkeley.edu",
                assignments="Homework 1, Homework 2",
                days="4,4",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

        policy = self.get_policy(
            mock_request=self.get_request(
                email="D4@berkeley.edu",
                assignments="Project 1 Checkpoint",
                days="2",
                has_partner="Yes",
                partner_email="D5@berkeley.edu",
                reason="test_flag_wip_for_student_with_partner",
            ),
            timestamp="2022-01-27T20:46:42.125Z",
        )
        assert not policy.apply(silent=True)

    #########################################################################################################
    # [E] Bad form configuration
    #########################################################################################################
    def test_assignment_missing(self):
        with pytest.raises(KnownError):
            policy = self.get_policy(
                mock_request=self.get_request(
                    email="D2@berkeley.edu",
                    assignments="Does Not Exist",
                    days="4,4",
                    reason="test_assignment_missing",
                ),
                timestamp="2022-01-27T20:46:42.125Z",
            )
            policy.apply(silent=True)

    def test_fail_cast_bool(self):
        with pytest.raises(KnownError):
            AssignmentList(
                sheet=MockSheet(
                    rows=[["Homework 1", "hw1", "2022-02-02", "False"]],
                    headers=["name", "id", "due_date", "partner"],
                    sheet=None,
                ),
            )

    #########################################################################################################
    # [F] Bad user inputs
    #########################################################################################################
    def test_invalid_num_days(self):
        with pytest.raises(KnownError):
            policy = self.get_policy(
                mock_request=self.get_request(email="D2@berkeley.edu", assignments="Homework 1", days="4,4,8"),
                timestamp="2022-01-27T20:46:42.125Z",
            )
            policy.apply(silent=True)

        with pytest.raises(KnownError):
            policy = self.get_policy(
                mock_request=self.get_request(
                    email="D2@berkeley.edu", assignments="Homework 1, Homework 2", days="4,4,8"
                ),
                timestamp="2022-01-27T20:46:42.125Z",
            )
            policy.apply(silent=True)

        with pytest.raises(KnownError):
            policy = self.get_policy(
                mock_request=self.get_request(email="D2@berkeley.edu", assignments="Homework 1", days="not a number"),
                timestamp="2022-01-27T20:46:42.125Z",
            )
            policy.apply(silent=True)
