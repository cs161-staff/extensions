# from main import handle_flush_gradescope

# from tests.MockRequest import MockRequest


# This test is problematic because it clears all environment variables, including those created during testing.
# This causes tests that are run after this one to fail.
# As such, we've commented it out for the time being.

# class TestFlush:
#     def test_handle_flush_gradescope(self):
#         handle_flush_gradescope(
#             MockRequest(
#                 payload={
#                     "spreadsheet_url": "https://docs.google.com/spreadsheets/d/136zB6RW8mhW4ryvquEy7utMD1cTP8ysF8pQu-ecPCJM/edit#gid=1603800846"
#                 }
#             )
#         )
