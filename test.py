"""
A file used for local testing.
"""

import json
from typing import Dict, Any

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
        "partner_auto.json",
        # "dsp_auto.json",
        # "regular_dne.json",
        # "partner_dne.json",
        # "retroactive.json",
    ]
    for test_file in tests:
        print("-" * 100)
        handle_form_submit(MockRequest(json.load(open("test_data/" + test_file))))


if __name__ == "__main__":
    test()
