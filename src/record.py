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
        self.write_queue = {}

    def has_wip_status(self):
        return (
            self.approval_status() == APPROVAL_STATUS_REQUESTED_MEETING
            or self.approval_status() == APPROVAL_STATUS_PENDING
        )

    def get_email(self):
        return self.table_record["email"].lower()

    def is_dsp(self):
        return self.table_record["is_dsp"] == "Yes"

    def get_email_comments(self) -> None:
        return self.table_record["email_comments"]

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
        self.write_queue[col_key] = col_value

    def flush(self):
        headers = self.sheet.get_headers()
        if "last_updated" in headers:
            self.write_queue["last_updated"] = PST.localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        if self.table_index == -1:
            print("Flushing student record, adding new row.")
            values = [self.write_queue.get(header) for header in headers]
            self.sheet.sheet.append_row(values=values)

            # Update local table_record object for email.
            for col, value in self.write_queue.items():
                self.table_record[col] = value

        else:
            print("Flushing student record, updating existing row.")
            for col, value in self.write_queue.items():
                row_index = self.table_index
                col_index = headers.index(col)
                self.sheet.update_cell(row_index=row_index, col_index=col_index, value=value)

                # Update local table_record object for email.
                self.table_record[col] = value

    @staticmethod
    def from_email(email: str, sheet_records: Sheet) -> StudentRecord:
        email = email.lower()
        query_result = sheet_records.get_record_by_id(id_column="email", id_value=email)
        if query_result:
            return StudentRecord(table_index=query_result[0], table_record=query_result[1], sheet=sheet_records)
        else:
            new_row = {header: "" for header in sheet_records.get_headers()}
            new_row["email"] = email
            new_record = StudentRecord(
                table_index=-1,
                table_record=new_row,
                sheet=sheet_records,
            )
            new_record.queue_write_back(col_key="email", col_value=email)
            return new_record
