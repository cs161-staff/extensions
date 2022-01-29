from __future__ import annotations
from datetime import datetime

from typing import Any, Dict, Optional
from src.assignments import AssignmentManager

from src.errors import FormInputError, StudentRecordError
from src.sheets import Sheet

APPROVAL_STATUS_REQUESTED_MEETING = "Requested Meeting"
APPROVAL_STATUS_PENDING = "Pending"
APPROVAL_STATUS_AUTO_APPROVED = "Auto Approved"
APPROVAL_STATUS_MANUAL_APPROVED = "Manually Approved"

EMAIL_STATUS_PENDING = "Pending Approval"
EMAIL_STATUS_IN_QUEUE = "In Queue"
EMAIL_STATUS_AUTO_SENT = "Auto Sent"
EMAIL_STATUS_MANUAL_SENT = "Manually Sent"

from datetime import datetime
from pytz import timezone

PST = timezone("US/Pacific")


class StudentRecord:
    """
    An object to hold a single student record (e.g. a row of the "Roster" summary sheet). These student records
    serve as the source of truth for the student's extensions.
    """

    def __init__(self, table_record: Dict[str, Any], table_index: int, sheet: Sheet) -> None:
        self.table_record = table_record
        self.table_index = table_index
        self.sheet = sheet
        self.write_queue = []

    def has_wip_status(self):
        return (
            self.approval_status() == APPROVAL_STATUS_REQUESTED_MEETING
            or self.approval_status() == APPROVAL_STATUS_PENDING
        )

    def get_name(self):
        return self.table_record["name"]

    def get_email(self):
        return self.table_record["email"].lower()

    def is_dsp(self):
        return self.table_record["is_dsp"] == "Yes"

    def get_status(self):
        return self.table_record["approval_status"]

    def get_email_comments(self) -> None:
        return self.table_record.get("email_comments")

    def get_email_status(self):
        return self.table_record["email_status"]

    def approval_status(self):
        return self.table_record["approval_status"]

    def email_status(self):
        return self.table_record["email_status"]

    def _queue_approval_status(self, status: str):
        self.queue_write_back(col_key="approval_status", col_value=status)

    def _queue_email_status(self, status: str):
        self.queue_write_back(col_key="email_status", col_value=status)

    def set_status_requested_meeting(self):
        self._queue_approval_status(APPROVAL_STATUS_REQUESTED_MEETING)
        self._queue_email_status("")

    def set_status_pending(self):
        self._queue_approval_status(APPROVAL_STATUS_PENDING)
        self._queue_email_status(EMAIL_STATUS_PENDING)

    def set_status_email_approved(self):
        self._queue_email_status(EMAIL_STATUS_AUTO_SENT)

    def set_status_approved(self):
        self._queue_approval_status(APPROVAL_STATUS_AUTO_APPROVED)
        self._queue_email_status(EMAIL_STATUS_AUTO_SENT)

    def existing_request_count(self, assignment_manager: AssignmentManager) -> Optional[int]:
        count = 0
        for assignment_id in assignment_manager.get_all_ids():
            if self.get_assignment(assignment_id=assignment_id):
                count += 1
        return count

    def get_assignment(self, assignment_id: str) -> Optional[int]:
        try:
            result = str(self.table_record[assignment_id])
            result = result.strip()
            if len(result) > 0:
                return int(result)
            return None
        except Exception as err:
            raise StudentRecordError(
                f"An error occurred while fetching assignment with ID {assignment_id}.\n"
                + f"Table Record: {self.table_record}\n"
                + f"Table Index: {self.table_index}\n"
                + f"Error: {err}"
            )

    def has_existing_request(self, assignment_id: str):
        if self.get_assignment(assignment_id=assignment_id):
            return True
        return False

    def queue_write_back(self, col_key: str, col_value: Any) -> Optional[str]:
        self.write_queue.append((col_key, col_value))

    def dispatch_writes(self):
        headers = self.sheet.get_headers()
        for col_key, value in self.write_queue:
            row_index = self.table_index
            col_index = headers.index(col_key)
            self.sheet.update_cell(row_index=row_index, col_index=col_index, value=value)
            # once writes are dispatched to backend, update the local object as well (this is so that it shows
            # up in the email that's generated)
            self.table_record[col_key] = value

        if "last_updated" in headers:
            row_index = self.table_index
            col_index = headers.index("last_updated")
            value = PST.localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            self.sheet.update_cell(row_index=row_index, col_index=col_index, value=value)
            self.table_record["last_updated"] = value

    @staticmethod
    def from_email(email: str, sheet_records: Sheet) -> StudentRecord:
        query_result = sheet_records.get_record_by_id(id_column="email", id_value=email)
        if not query_result:
            raise FormInputError(f"This student's email was not found: {email}")
        return StudentRecord(table_index=query_result[0], table_record=query_result[1], sheet=sheet_records)
