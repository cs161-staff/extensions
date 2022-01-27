"""
A file used for local testing.
"""

import json

from src.handle_form_submit import handle_form_submit
from src.handle_email_queue import handle_email_queue
from src.sheets import Sheet

import gspread


def test():
    handle_form_submit(json.load(open("test_data/test.json")))


if __name__ == "__main__":
    test()
