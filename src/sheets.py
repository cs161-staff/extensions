import os
from typing import Any, Dict, List, Optional, Tuple

import gspread
from gspread.worksheet import Worksheet

from src.errors import SheetError

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
        self.all_values = self.sheet.get_all_values()
        self.all_records = self.sheet.get_all_records()
        self.headers = self.all_values[0]

    def get_headers(self) -> List[str]:
        return self.headers

    def get_all_values(self) -> List[List[Any]]:
        return self.all_values

    def get_all_records(self) -> List[Dict[str, Any]]:
        return self.all_records

    def get_record_by_id(self, id_column: str, id_value: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        all_records = self.get_all_records()
        for i, record in enumerate(all_records):
            if str(record.get(id_column)).lower() == str(id_value).lower():
                return (i, record)
        return None

    def update_cells(self, cells: List[Any]):
        gspread_cells: List[gspread.Cell] = []
        for row, col, value in cells:
            gspread_cells.append(gspread.Cell(row=row + 2, col=col + 1, value=value))
        if len(gspread_cells) > 0:
            self.sheet.update_cells(gspread_cells, value_input_option="USER_ENTERED")

    def update_cell(self, row_index: int, col_index: int, value: Any) -> Dict[str, Any]:
        """
        Note: pass in data-relative row_index and col_index here. This method offsets row_index by two,
        to account for a header row and gspread's one-indexing, and col_index by one, to account for
        gspread's one-indexing. For example, to update the first student record's first cell, pass in (0, 0).
        """
        row = row_index + 2
        col = col_index + 1
        self.sheet.update_cell(row, col, value)

    def append_row(self, values: List[Any], value_input_option: str):
        self.sheet.append_row(values=values, value_input_option=value_input_option)


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
