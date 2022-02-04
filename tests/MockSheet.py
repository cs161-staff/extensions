from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import gspread
from gspread.worksheet import Worksheet
from src.errors import SheetError

SHEET_STUDENT_RECORDS = "Roster"
SHEET_ASSIGNMENTS = "Assignments"
SHEET_FORM_QUESTIONS = "Form Questions"
SHEET_ENVIRONMENT_VARIABLES = "Environment Variables"

import pandas as pd


class MockSheet:
    """
    A wrapper around a Google Sheets "sheet" (e.g. one tab of a spreadsheet).
    """

    def __init__(self, rows: List[List[str]], headers: List[str], sheet: Worksheet) -> None:
        self.df = pd.DataFrame(rows, columns=headers)
        self.headers = headers
        self.all_values = [headers] + rows
        self.all_records = []
        for row in rows:
            self.all_records.append({key: row[i] for i, key in enumerate(headers)})
        self.sheet = sheet

    @staticmethod
    def from_live(sheet: Worksheet) -> MockSheet:
        rows = sheet.get_all_values()
        return MockSheet(rows=rows[1:], headers=rows[0], sheet=sheet)

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
        for row, col, value in cells:
            if col > len(self.df):
                self.df.append([])
            self.df.loc[row][self.headers[col]] = value

    def flush(self):
        cells: List[gspread.Cell] = []
        for i, row in self.df.iterrows():
            for j, col in enumerate(self.df.columns):
                cells.append(gspread.Cell(row=i + 2, col=j + 1, value=row[col]))
        self.sheet.update_cells(cells, value_input_option="USER_ENTERED")
        print(self.sheet.get_all_values())

    def append_row(self, values: List[Any], value_input_option: str):
        self.df.loc[len(self.df)] = values
