import functools
import http.client
import json
import logging
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
        "default": """
        <html><head><style>body{color:white;text-align: center;background-color:[[=color]];font-family:serif} h1{font-size:6em;margin:16vh 0 8vh 0} h2{font-size:2em;margin:8vh 0} a{color:white;text-decoration:none;font-weight:bold;padding:10px 10px;border-radius:10px;border:2px solid #fff;transition: all .5s ease} a:hover{background:rgba(0,0,0,0.1);padding:10px 30px}</style></head>
        <body>
        <h1>[[=code]]</h1>
        <h2>[[=message]]</h2>
        [[if button_text:]]<a href="[[=href]]">[[=button_text]]</a>
        [[pass]]
        [[if traceback:]]
        <pre style="padding: 20px; margin-top: 20px; text-align: left; background: black">[[=traceback]]</pre>
        [[pass]]
        </body></html>
        """,
        "DumpDieError": """
        <html><body><pre>[[=str(exception)]]</pre></body></html>
        """,
        "FancyDumpDieError": """
        <html><head><link href="https://cdn.jsdelivr.net/npm/json-browse@0.2.0/json-browse/jquery.json-browse.css" rel="stylesheet"/></head>
        <body>
        <!-- https://www.jsdelivr.com/package/npm/json-browse?path=json-browse -->
        <pre id="json-renderer" class="json-body"></pre>
        <script src="https://code.jquery.com/jquery-3.6.1.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/json-browse@0.2.0/json-browse/jquery.json-browse.js"></script>
        <script>$('#json-renderer').jsonBrowse([[=XML(str(exception))]]);</script>
        </body></html>
        """,
        "ApiDumpDieError": None,
    }

    _tmpl = templates.get(err_type, templates["default"])

    context["XML"] = XML

    if _tmpl is None:
        # just bare exception
        return str(context["exception"])

    return yatl.render(
        _tmpl,
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
