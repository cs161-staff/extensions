from typing import List
from src.assignments import AssignmentManager
from src.record import StudentRecord
from src.submission import FormSubmission
from slack_sdk.webhook import WebhookClient, WebhookResponse

from src.errors import SlackError
from src.utils import Environment
from tabulate import tabulate


class SlackManager:
    """
    A container to hold Slack-related utilities.
    """

    def __init__(self) -> None:
        self.webhooks: List[WebhookClient] = []
        self.webhooks.append(WebhookClient(Environment.get("SLACK_ENDPOINT")))
        self.warnings = []

        if Environment.contains("SLACK_ENDPOINT_DEBUG"):
            if Environment.get("SLACK_ENDPOINT_DEBUG") != Environment.get("SLACK_ENDPOINT"):
                self.webhooks.append(WebhookClient(Environment.get("SLACK_ENDPOINT_DEBUG")))

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def _get_submission_details_knows_assignments(self):
        text = "> *Email*: " + self.submission.get_email() + "\n"
        text += "> *Assignment(s)*: " + self.submission.get_raw_requests() + "\n"
        text += "> *Days*: " + self.submission.get_raw_days() + "\n"
        text += "> *Reason*: " + self.submission.get_reason() + "\n"
        if self.submission.claims_dsp():
            text += "> *DSP Accomodations for Extensions*: " + self.submission.dsp_status() + "\n"
        if self.submission.has_partner():
            text += "> *Partner Email*: " + self.submission.get_partner_email() + "\n"
        return text

    def _get_submission_details_unknown_assignments(self):
        text = "> *Email*: " + self.submission.get_email() + "\n"
        text = "> *Notes*: " + self.submission.get_game_plan() + "\n"
        return text

    def set_current_student(
        self, submission: FormSubmission, student: StudentRecord, assignment_manager: AssignmentManager
    ):
        self.submission = submission
        self.student = student
        self.assignment_manager = assignment_manager

    def send_message(self, message: str) -> None:
        for webhook in self.webhooks:
            response = webhook.send(text=message)
            self.check_error(response)

    def send_student_update(self, message: str, autoapprove: bool = False) -> None:
        message += "\n"
        if self.submission.knows_assignments():
            message += self._get_submission_details_knows_assignments()
        else:
            message += self._get_submission_details_unknown_assignments()

        message += "\n"
        message += "This student's extension request summary is below:"
        headers = ["Assignment", "# Days Requested"]
        rows = []
        for assignment_id in self.assignment_manager.get_all_ids():
            num_days = self.student.get_assignment(assignment_id)
            if num_days:
                rows.append([self.assignment_manager.id_to_name(assignment_id), num_days])
        message += "```"
        message += tabulate(rows, headers=headers)
        message += "```"
        message += "\n"
        message += "\n"
        if len(self.warnings) > 0:
            message += "*Warnings:*\n"
            message += "```" + "\n"
            for w in self.warnings:
                message += w + "\n"
            message += "```"

        if autoapprove:
            for webhook in self.webhooks:
                response = webhook.send(text=message)
                self.check_error(response)
        else:
            for webhook in self.webhooks:
                response = webhook.send(
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": message}},
                        {
                            "type": "actions",
                            "block_id": "approve_extension",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "View Spreadsheet"},
                                    "url": Environment.get("SPREADSHEET_URL"),
                                },
                            ],
                        },
                    ]
                )
                self.check_error(response)

    def send_error(self, error: str) -> None:
        for webhook in self.webhooks:
            webhook.send(text="An error occurred: " + "\n" + "```" + "\n" + error + "\n" + "```")

    def check_error(self, response: WebhookResponse):
        if response.status_code != 200:
            raise SlackError(f"Status code not 200: {vars(response)}")
