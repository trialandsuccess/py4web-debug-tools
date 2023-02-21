import functools
import http.client
import json
import logging
import os
import re
import traceback

import ombott as bottle
import yatl
from py4web import action, response, HTTP
from py4web.core import (
    dumps,
    request,
    error_logger,
    get_error_snapshot,
    REGEX_APPJSON,
    Template,
)
from yatl import XML


def custom_error_page(
    code,
    button_text=None,
    href="#",
    color=None,
    message=None,
    traceback="",
    err_type=None,
    bare_exception=None,
):
    if not isinstance(err_type, str):
        err_type = err_type.__name__

    if hasattr(Template, "_on_success"):
        # reset here on error, because on_error might not be called!
        Template.on_success = Template._on_success
        del Template._on_success

    message = http.client.responses[code].upper() if message is None else message
    color = (
        {"4": "#F44336", "5": "#607D8B"}.get(str(code)[0], "#2196F3")
        if not color
        else color
    )
    context = dict(
        code=code,
        message=message,
        button_text=button_text,
        href=href,
        color=color,
        traceback=traceback,
        err_type=err_type,
        exception=bare_exception,
    )
    # if client accepts 'application/json' - return json
    if re.search(REGEX_APPJSON, request.headers.get("accept", "")):
        response.status = code
        return json.dumps(context)
    # else - return html error-page

    templates = {
        "default": "error_default.html",
        "DumpDieError": "dumpdie.html",
        "FancyDumpDieError": "fancy_dumpdie.html",
        "ApiDumpDieError": None,
    }

    _tmpl = templates.get(err_type, templates["default"])

    if _tmpl is None:
        # just bare exception
        return str(context["exception"])

    context["XML"] = XML

    fname = os.path.join(os.path.dirname(__file__), "templates", _tmpl)
    with open(fname) as f:
        return yatl.render(
            stream=f,
            context=context,
            delimiters="[[ ]]",
        )


def custom_catch_errors(app_name, func):
    """Catches and logs errors in an action; also sets request.app_name"""

    @functools.wraps(func)
    def wrapper(*func_args, **func_kwargs):
        try:
            request.app_name = app_name
            ret = func(*func_args, **func_kwargs)
            if isinstance(ret, dict):
                response.headers["Content-Type"] = "application/json"
                ret = dumps(ret)
            return ret
        except HTTP as http:
            response.status = http.status
            response.headers.update(http.headers)
            return http.body
        except bottle.HTTPResponse:
            raise
        except Exception as e:
            snapshot = get_error_snapshot()
            logging.error(snapshot["traceback"])
            ticket_uuid = error_logger.log(request.app_name, snapshot) or "unknown"
            response.status = 500

            raise bottle.HTTPResponse(
                body=custom_error_page(
                    500,
                    button_text=ticket_uuid,
                    href="/_dashboard/ticket/" + ticket_uuid,
                    traceback=traceback.format_exc(),
                    err_type=type(e),
                    bare_exception=e,
                ),
                status=500,
            )

    return wrapper


def patch_py4():
    action.catch_errors = custom_catch_errors
