from src.assignments import AssignmentList
from src.errors import ConfigurationError
from src.gradescope import Gradescope
from src.record import StudentRecord
from src.sheets import SHEET_ASSIGNMENTS, SHEET_ENVIRONMENT_VARIABLES, SHEET_STUDENT_RECORDS, BaseSpreadsheet
from src.slack import SlackManager
from src.utils import Environment


def handle_flush_gradescope(request_json):
    if "spreadsheet_url" not in request_json:
        raise ConfigurationError("handle_flush_gradescope expects spreadsheet_url parameter")

    # Get pointers to sheets.
    base = BaseSpreadsheet(spreadsheet_url=request_json["spreadsheet_url"])
    sheet_assignments = base.get_sheet(SHEET_ASSIGNMENTS)
    sheet_records = base.get_sheet(SHEET_STUDENT_RECORDS)
    sheet_env_vars = base.get_sheet(SHEET_ENVIRONMENT_VARIABLES)

    # Set up environment variables.
    Environment.configure_env_vars(sheet_env_vars)

    # Fetch assignments.
    assignments = AssignmentList(sheet=sheet_assignments)

    # Fetch records.
    records = sheet_records.get_all_records()

    slack = SlackManager()

    gradescope = Gradescope()

    all_warnings = []
    successes = []
    failures = []
    for i, table_record in enumerate(records):
        student = StudentRecord(table_index=i, table_record=table_record, sheet=sheet_records)
        if student.should_flush_gradescope():
            warnings = student.apply_extensions(assignments=assignments, gradescope=gradescope)
            if len(warnings) > 0:
                failures.append(student.get_email())
                all_warnings.extend(warnings)
            else:
                successes.append(student.get_email())
                student.set_flush_gradescope_status_success()

        student.flush()

    for warning in all_warnings:
        slack.add_warning(warning)

    summary = "Flush Gradescope Summary:" + "\n"
    if len(successes) > 0:
        summary += "\n" + "*Successes:* " + ", ".join(successes)
    if len(failures) > 0:
        summary += "\n" + "*Failures:* " + ", ".join(failures)
    if len(successes) + len(failures) == 0:
        summary += (
            "\n"
            + "No student records processed. To process a student record, create a `flush_gradescope` column on the Roster sheet, and set the value to TRUE for each record you would like to flush to Gradescope."
        )

    slack.send_message(summary)
