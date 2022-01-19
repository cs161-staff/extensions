"""
A file used for local testing.
"""

import json

from src.handle_form_submit import handle_form_submit
from src.handle_email_queue import handle_email_queue
from src.sheets import Sheet

import gspread

def test_email():
    handle_email_queue({
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459",
    })

def test():
    handle_form_submit(json.load(open("test_data/knows_assignments.json")))

def rerun_records():
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459"
    worksheet = gspread.service_account("service-account.json").open_by_url(spreadsheet_url).worksheet('Form Responses')
    sheet = Sheet(sheet=worksheet)
    for record in sheet.get_all_records():
        if record.get('Rerun') == 'TRUE':
            print('-'*100)
            handle_form_submit({
                'spreadsheet_url': spreadsheet_url,
                'form_data': {k: [v] for k, v in record.items()}
            })


if __name__ == "__main__":
    test_email()
