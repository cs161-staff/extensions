"""
A file used for local testing.
"""

import json
from dotenv import load_dotenv

from src.handle_form_submit import handle_form_submit
from src.handle_email_queue import handle_email_queue

load_dotenv()  # take environment variables from .env.


def test():
    # handle_form_submit(
    #     {
    #         "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459",
    #         "form_data": json.load(open("test_data/knows_assignments.json")),
    #     }
    # )
    handle_email_queue({
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459",
    })


if __name__ == "__main__":
    test()
