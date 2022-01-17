from dotenv import load_dotenv

from core.errors import ExtensionsError
from core import form, email

load_dotenv()  # take environment variables from .env.

def handle_email_queue(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    try:
        email.process_email_queue(request_json=request_json)
        return {"success": True}
    except ExtensionsError as e:
        # TODO: Send a Slack message.
        print("Known Error Occurred: " + str(e))
        return {"success": False, "error": str(e)}
    except Exception as e:
        # TODO: Send a Slack message.
        raise

def handle_form_submit(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    try:
        form.handle_form_submit(request_json=request_json)
        return {"success": True}
    except ExtensionsError as e:
        # TODO: Send a Slack message.
        print("Known Error Occurred: " + str(e))
        return {"success": False, "error": str(e)}
    except Exception as e:
        # TODO: Send a Slack message.
        raise
