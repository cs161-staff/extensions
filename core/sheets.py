from __future__ import print_function

from typing import Any, Dict, List

from gspread.spreadsheet import Spreadsheet


def extract_records(table: List[List[Any]], index_by: str, include_row_number: bool = True):
    if len(table) <= 1:
        return []
    headers, rows = table[0], table[1:]
    data = [{headers[i]: value for i, value in enumerate(row)} for row in rows]
    if include_row_number:
        return {row[index_by]: (i, row) for i, row in enumerate(data)}
    else:
        return {row[index_by]: row for row in data}


def extract_headers(table: List[List[Any]]) -> Dict[str, int]:
    return {header: i for i, header in enumerate(table[0])}


def extract_config(table: List[List[Any]]):
    if len(table) <= 1:
        return []
    return {row[0]: row[1] for row in table[1:]}


def fetch_table(spreadsheet: Spreadsheet, name: str) -> Dict:
    table = spreadsheet.worksheet(name).get_all_values()
    return table
