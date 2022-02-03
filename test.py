"""
A file used for local testing.
"""

import json
from typing import Dict, Any
import sys

# for testing Gradescope package currently under development
# in production, we will use the gradescope_api from https://cs161-staff/gradescope-api
sys.path.append("/Users/shomil/Documents/github/cs161-staff/notebook/gradescope-api/src/")

from main import handle_form_submit


class MockRequest:
    def __init__(self, json: Dict[str, Any]) -> None:
        self.json = json

    def get_json(self):
        return self.json


def test():
    # tests = ["regular_dne.json", "partner_dne.json"]
    # tests = ["regular_auto.json"]
    tests = [
        # "student_meeting.json",
        # "regular_auto.json",
        # "regular_manual.json",
        # "partner_auto.json",
        # "dsp_auto.json",
        # "retroactive.json",
        "gs_extend.json"
    ]
    for test_file in tests:
        print("-" * 100)
        handle_form_submit(MockRequest(json.load(open("test_data/" + test_file))))


if __name__ == "__main__":
    test()
