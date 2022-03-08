from main import handle_flush_gradescope

from tests.MockRequest import MockRequest


class TestFlush:
    def test_handle_flush_gradescope(self):
        handle_flush_gradescope(
            MockRequest(
                payload={
                    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/136zB6RW8mhW4ryvquEy7utMD1cTP8ysF8pQu-ecPCJM/edit#gid=1603800846"
                }
            )
        )
