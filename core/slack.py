import os
from typing import Any, Dict
from slack_sdk.webhook import WebhookClient
from tabulate import tabulate

from core.utils import cast_bool


def get_form_details(form: Dict[str, Any]):
    text = ""
    text += "> *Email*: " + form["email"] + "\n"
    text += "> *Assignment(s)*: " + form["assignments"] + "\n"
    text += "> *Days*: " + form["days"] + "\n"
    text += "> *Reason*: " + form["reason"] + "\n"

    if cast_bool(form["has_partner"]):
        text += "> *Partner Email*: " + form["partner_email"] + "\n"
    return text


def send_auto_approved(student_record: Dict[str, Any], form: Dict[str, Any]):
    webhook = WebhookClient(os.environ.get("SLACK_ENDPOINT"))
    text = "An extension request was auto-approved. Details:" + "\n"
    text += get_form_details(form)
    webhook.send(text=text)


def send_needs_manual_approval(
    spreadsheet_url: str, student_record: Dict[str, Any], all_assignments: Dict[str, Any], form: Dict[str, Any]
):
    webhook = WebhookClient(os.environ.get("SLACK_ENDPOINT"))
    text = "An extension request could not be auto-approved. Details:" + "\n"
    text += get_form_details(form) + "\n"
    text += "This student's extension request summary is below:"

    headers = ["Assignment", "# Days Requested"]
    rows = []
    for assignment in all_assignments.values():
        assignment_id = assignment["id"]
        if student_record[assignment_id]:
            rows.append([assignment["name"], student_record[assignment_id]])
    text += "```"
    text += tabulate(rows, headers=headers)
    text += "```"

    response = webhook.send(
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {
                "type": "actions",
                "block_id": "approve_extension",
                "elements": [
                    # {
                    #     "type": "button",
                    #     "text": {"type": "plain_text", "text": "Approve"},
                    #     "style": "primary",
                    #     "value": student_record["sid"],
                    # },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Spreadsheet"},
                        "url": spreadsheet_url,
                    },
                ],
            },
        ]
    )
    print(response.body)
