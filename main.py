from src.errors import KnownError

import src.handle_email_queue as handle_email
import src.handle_form_submit as handle_form
from src.slack import SlackManager


def handle_email_queue(request):
    request_json = request.get_json()
    try:
        handle_email.handle_email_queue(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e))
        SlackManager().send_error(str(e) + f' (Request: {request_json})')
        return {"success": False, "error": str(e)}
    except Exception as e:
        # TODO: Send a Slack message.
        raise


def handle_form_submit(request):
    request_json = request.get_json()
    try:
        handle_form.handle_form_submit(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        # TODO: Send a Slack message.
        print("Known Error Occurred: " + str(e))
        SlackManager().send_error(str(e) + f' (Request: {request_json})')
        return {"success": False, "error": str(e)}
    except Exception as e:
        # TODO: Send a Slack message.
        raise
