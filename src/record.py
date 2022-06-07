from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from dateutil.parser import parse
from pytz import timezone

from src.assignments import AssignmentList
from src.errors import StudentRecordError
from src.gradescope import Gradescope
from src.sheets import Sheet
from src.utils import cast_bool

APPROVAL_STATUS_REQUESTED_MEETING = "Requested Meeting"
APPROVAL_STATUS_PENDING = "Pending"
APPROVAL_STATUS_AUTO_APPROVED = "Auto Approved"

EMAIL_STATUS_PENDING = "Pending Approval"
EMAIL_STATUS_IN_QUEUE = "In Queue"
EMAIL_STATUS_AUTO_SENT = "Auto Sent"

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

    def roster_contains_dsp_status(self):
        return "is_dsp" in self.table_record

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

    def set_log(self, log: str):
        if "last_run_output" in self.sheet.get_headers():
            self.queue_write_back(col_key="last_run_output", col_value=log)

    def set_last_run_reason(self, reason: str):
        if "last_run_reason" in self.sheet.get_headers():
            self.queue_write_back(col_key="last_run_reason", col_value=str(reason).replace("\n", " "))

    def set_status_requested_meeting(self):
        self._queue_approval_status(APPROVAL_STATUS_REQUESTED_MEETING)
        self._queue_email_status("")

    def set_status_pending(self):
        if self.approval_status() != APPROVAL_STATUS_REQUESTED_MEETING:
            self._queue_approval_status(APPROVAL_STATUS_PENDING)
            self._queue_email_status(EMAIL_STATUS_PENDING)

    def set_status_email_approved(self):
        self._queue_email_status(EMAIL_STATUS_AUTO_SENT)

    def set_status_approved(self):
        self._queue_approval_status(APPROVAL_STATUS_AUTO_APPROVED)
        self._queue_email_status(EMAIL_STATUS_AUTO_SENT)

    def should_flush_gradescope(self):
        if "flush_gradescope" in self.sheet.get_headers():
            return cast_bool(self.table_record["flush_gradescope"])
        return False

    def set_flush_gradescope_status_success(self):
        if "flush_gradescope" in self.sheet.get_headers():
            self.queue_write_back(col_key="flush_gradescope", col_value=False)

    def count_requests(self, assignments=AssignmentList):
        count = 0
        for assignment_id in assignments.get_all_ids():
            if self.get_request(assignment_id=assignment_id) is not None:
                count += 1
        return count

    def get_request(self, assignment_id: str) -> Optional[int]:
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

    def queue_write_back(self, col_key: str, col_value: Any) -> Optional[str]:
        self.write_queue[col_key] = col_value

    def set_last_run_timestamp(self, timestamp: str):
        if "last_run_timestamp" in self.sheet.get_headers():
            timestamp: datetime = parse(timestamp)
            if not timestamp.tzinfo:
                timestamp = PST.localize(timestamp)
            self.queue_write_back(
                col_key="last_run_timestamp", col_value=str(timestamp.strftime("%-m/%-d/%Y %H:%M:%S"))
            )

    def flush(self):
        headers = self.sheet.get_headers()

        if self.table_index == -1:
            values = [self.write_queue.get(header) for header in headers]
            self.sheet.append_row(values=values, value_input_option="USER_ENTERED")

            # Update local table_record object for email.
            for col, value in self.write_queue.items():
                self.table_record[col] = value

        else:
            cells = []
            for col, value in self.write_queue.items():
                row_index = self.table_index
                col_index = headers.index(col)
                cells.append([row_index, col_index, value])

                # Update local table_record object for email.
                self.table_record[col] = value
            self.sheet.update_cells(cells=cells)

    def apply_extensions(self, assignments: AssignmentList, gradescope: Gradescope) -> List[str]:
        warnings = []
        for assignment in assignments:
            num_days = self.get_request(assignment_id=assignment.get_id())
            if num_days:
                if len(assignment.get_gradescope_assignment_urls()) == 0:
                    print(
                        f"[{assignment.get_name()}] could not extend assignment deadline for {self.get_email()} (assignment URL's not set)."
                    )
                    continue

                elif not assignment.get_due_date():
                    warnings.append(
                        f"[{assignment.get_name()}] could not extend assignment deadline for {self.get_email()} (deadline not set)."
                    )
                    continue

                else:
                    print("Extending assignments: " + str(assignment.get_gradescope_assignment_urls()))
                    warnings = gradescope.apply_extension(
                        assignment_urls=assignment.get_gradescope_assignment_urls(),
                        email=self.get_email(),
                        num_days=num_days,
                    )
                    warnings.extend(warnings)
        return warnings

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
