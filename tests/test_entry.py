from main import handle_form_submit

from tests.MockRequest import MockRequest


class TestEntry:
    def test_handle_form_submit(self):
        handle_form_submit(
            MockRequest(
                payload={
                    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit",
                    "form_data": {
                        "Timestamp": ["2021-05-28T23:19:02.074Z"],
                        "Student ID Number": [123456],
                        "Email Address": ["shomil+cs161test@berkeley.edu"],
                        "Are you a DSP student with an accommodation for assignment extensions?": ["No"],
                        "Do you know what assignments(s) you need extensions on?": ["Yes"],
                        "Which assignment would you like an extension on?": ["Project 3 (Code/Writeup)"],
                        "How many days would you like an extension for?": [2],
                        "Why do you need this extension?": ["Test case: a simple, auto-approved extension."],
                        # "Are you working with one (or more) partners on this assignment?": ["No"],
                        # "What is your partner's email?": [""],
                        # "What is your partner's Student ID?": [""],
                        "About how long do you think you will have issues? When are you free to chat with a TA to make a game plan for the class?": [
                            ""
                        ],
                        "Rerun": [True],
                        "": [None],
                    },
                }
            )
        )
