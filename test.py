"""
A file used for local testing.
"""

import json
from dotenv import load_dotenv

from core import form, email

load_dotenv()  # take environment variables from .env.


def test():
    form.handle_form_submit(
        {
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459",
            "form_data": json.load(open("test_data/knows_assignments.json")),
        }
    )
    # email.process_email_queue({
    #     "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1MsGh1OFPltaoXGF8kv0e-O9WAFoaxcbFA6HVM7AbFOQ/edit?resourcekey#gid=790260459",
    # })


if __name__ == "__main__":
    test()
