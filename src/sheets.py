import os
from typing import Any, Dict, List, Optional, Tuple
import gspread

from src.errors import ConfigurationError, SheetError
from gspread.worksheet import Worksheet

SHEET_STUDENT_RECORDS = "Roster"
SHEET_ASSIGNMENTS = "Assignments"
SHEET_FORM_QUESTIONS = "Form Questions"
SHEET_ENVIRONMENT_VARIABLES = "Environment Variables"


class Sheet:
    """
    A wrapper around a Google Sheets "sheet" (e.g. one tab of a spreadsheet).
    """

    def __init__(self, sheet: Worksheet) -> None:
        self.sheet: Worksheet = sheet

    def get_headers(self) -> List[str]:
        table = self.sheet.get_all_values()
        if len(table) > 1:
            return table[0]
        raise ConfigurationError("Too few values in sheet...")

    def get_all_values(self) -> List[List[Any]]:
        return self.sheet.get_all_values()

    def get_all_records(self) -> List[Dict[str, Any]]:
        return self.sheet.get_all_records(numericise_ignore=['all'])

    def get_record_by_id(self, id_column: str, id_value: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        all_records = self.get_all_records()
        for i, record in enumerate(all_records):
            if record.get(id_column) == id_value:
                return (i, record)
        return None

    def update_cell(self, row_index: int, col_index: int, value: Any) -> Dict[str, Any]:
        """
        Note: pass in data-relative row_index and col_index here. This method offsets row_index by two,
        to account for a header row and gspread's one-indexing, and col_index by one, to account for
        gspread's one-indexing. For example, to update the first student record's first cell, pass in (0, 0).
        """
        row = row_index + 2
        col = col_index + 1
        self.sheet.update_cell(row, col, value)


class BaseSpreadsheet:
    """
    A pointer to the master spreadsheet.
    """

    def __init__(self, spreadsheet_url: str) -> None:
        if not os.path.exists("service-account.json"):
            raise SheetError("Could not find Google Service Account at service-account.json.")

        self.spreadsheet_url = spreadsheet_url
        self.spreadsheet = gspread.service_account("service-account.json").open_by_url(spreadsheet_url)

    def get_sheet(self, sheet_name: str) -> Sheet:
        return Sheet(sheet=self.spreadsheet.worksheet(sheet_name))
