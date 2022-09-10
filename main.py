import json

import src.handle_email_queue as handle_email
import src.handle_flush_gradescope as handle_flush
import src.handle_form_submit as handle_form
from src.errors import KnownError
from src.slack import SlackManager
from src.utils import Environment, truncate


def handle_email_queue(request):
    request_json = request.get_json()
    print("handle_email_queue called on payload: " + json.dumps(request_json))
    try:
        handle_email.handle_email_queue(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error(str(e) + f" (Request: {truncate(request_json)})")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print("Internal Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error("Internal error: " + str(e) + f" (Request: {truncate(request_json)})")
        raise
    finally:
        Environment.clear()


def handle_flush_gradescope(request):
    request_json = request.get_json()
    print("handle_flush_gradescope called on payload: " + json.dumps(request_json))
    try:
        handle_flush.handle_flush_gradescope(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error(str(e) + f" (Request: {truncate(request_json)})")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print("Internal Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error("Internal error: " + str(e) + f" (Request: {truncate(request_json)})")
        raise
    finally:
        Environment.clear()


def handle_form_submit(request):
    request_json = request.get_json()
    print("handle_form_submit called on payload: " + json.dumps(request_json))
    try:
        handle_form.handle_form_submit(request_json=request_json)
        return {"success": True}
    except KnownError as e:
        print("Known Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error(str(e) + f" (Request: {truncate(request_json)})")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print("Internal Error Occurred: " + str(e) + f" (Request: {request_json})")
        SlackManager().send_error("Internal error: " + str(e) + f" (Request: {truncate(request_json)})")
        raise
    finally:
        Environment.clear()
