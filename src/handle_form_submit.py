from src.errors import ConfigurationError
from src.policy import Policy
from src.sheets import (
    SHEET_ASSIGNMENTS,
    SHEET_ENVIRONMENT_VARIABLES,
    SHEET_FORM_QUESTIONS,
    SHEET_STUDENT_RECORDS,
    BaseSpreadsheet,
)
from src.slack import SlackManager
from src.utils import Environment


def handle_form_submit(request_json):
    if "spreadsheet_url" not in request_json or "form_data" not in request_json:
        raise ConfigurationError("handle_form_submit expects spreadsheet_url/form_data parameters")

    # Get a pointer to the spreadsheet in the request.
    base = BaseSpreadsheet(spreadsheet_url=request_json["spreadsheet_url"])

    # Validate/configure environment variables
    Environment.configure_env_vars(sheet=base.get_sheet(SHEET_ENVIRONMENT_VARIABLES))

    # Get a pointer to Slack.
    slack = SlackManager()

    policy = Policy(
        sheet_assignments=base.get_sheet(SHEET_ASSIGNMENTS),
        sheet_form_questions=base.get_sheet(SHEET_FORM_QUESTIONS),
        form_payload=request_json["form_data"],
        slack=slack,
    )
    policy.fetch_student_records(sheet_records=base.get_sheet(SHEET_STUDENT_RECORDS))
    policy.apply()
