import src.handle_email_queue as handle_email
import src.handle_form_submit as handle_form
from src.errors import KnownError
from src.slack import SlackManager
from src.utils import Environment


def handle_email_queue(request):
    request_json = request.get_json()
    try:
        handle_email.handle_email_queue(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error(str(e) + f" (Request: {request_json})")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print("Internal Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error("Internal error: " + str(e) + f" (Request: {request_json})")
        raise
    finally:
        Environment.clear()


def handle_form_submit(request):
    request_json = request.get_json()
    try:
        handle_form.handle_form_submit(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error(str(e) + f" (Request: {request_json})")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print("Internal Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error("Internal error: " + str(e) + f" (Request: {request_json})")
        raise
