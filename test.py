"""
A file used for local testing.
"""

import json

from src.handle_form_submit import handle_form_submit


def test():
    tests = ["student_meeting.json", "regular_auto.json", "regular_manual.json", "partner_auto.json", "dsp_auto.json"]
    for test_file in tests:
        print("-" * 100)
        handle_form_submit(json.load(open("test_data/" + test_file)))


if __name__ == "__main__":
    test()
