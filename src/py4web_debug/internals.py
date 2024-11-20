import functools
import http.client
import json
import logging
import os
import re
import traceback as tb
import typing

import ombott as bottle
import yatl
from ombott import HTTPResponse
from py4web import HTTP, action, response
from py4web.core import (
    REGEX_APPJSON,
    Template,
    dumps,
    error_logger,
    get_error_snapshot,
    request,
)
from typing_extensions import NotRequired
from yatl import XML

from .types import ErrorSnapshot


class ContextDict(typing.TypedDict):
    code: int
    message: typing.Optional[str]
    button_text: typing.Optional[str]
    href: str
    color: typing.Optional[str]
    traceback: str
    err_type: str
    exception: typing.Optional[Exception | str]

    XML: NotRequired[typing.Type[XML]]


T_Renderer = typing.Callable[[ContextDict], str] | typing.Literal[False]
AnyFunc = typing.Callable[..., typing.Any]


def custom_error_page(
    code: int,
    button_text: str = None,
    href: str = "#",
    color: str = None,
    message: str = None,
    traceback: str = "",
    err_type: str | typing.Type[Exception] | None = None,
    bare_exception: typing.Optional[Exception | str] = None,
    renderer: T_Renderer = None,
) -> str:
    if err_type and not isinstance(err_type, str):
        err_type = err_type.__name__

    # make sure the name is a string (but it probably already is:)
    err_type_name = str(err_type)

    if hasattr(Template, "_on_success"):
        # reset here on error, because on_error might not be called!
        Template.on_success = Template._on_success
        del Template._on_success

    message = http.client.responses[code].upper() if message is None else message
    color = color or {"4": "#F44336", "5": "#607D8B"}.get(str(code)[0], "#2196F3")
    context: ContextDict = dict(
        code=code,
        message=message,
        button_text=button_text,
        href=href,
        color=color,
        traceback=traceback,
        err_type=err_type_name,
        exception=bare_exception,
    )
    # if client accepts 'application/json' - return json
    if re.search(REGEX_APPJSON, request.headers.get("accept", "")):
        response.status = code
        return json.dumps(context)
    # else - return html error-page

    if renderer:
        return renderer(context)

    templates = {
        "default": "error_default.html",
        "DumpDieError": "dumpdie.html",
        "FancyDumpDieError": "fancy_dumpdie.html",
        "ApiDumpDieError": None,
    }

    _tmpl = templates.get(err_type_name, templates["default"])

    if _tmpl is None:
        # just bare exception
        return str(context["exception"])

    context["XML"] = XML

    fname = os.path.join(os.path.dirname(__file__), "templates", _tmpl)
    with open(fname) as f:
        result = yatl.render(
            stream=f,
            context=context,
            delimiters="[[ ]]",
        )
    return typing.cast(str, result)


def default_error_logger(snapshot: ErrorSnapshot) -> None:
    logging.error(snapshot["traceback"])


T_Logger = typing.Callable[[ErrorSnapshot], None]


class patch_py4:
    # THIS IS ONLY CALLED ONCE, WHEN tools.enable IS CALLED OR py4web_debug.wsgi IS USED!
    renderer: T_Renderer | None = None
    logger: T_Logger | typing.Literal[False] | None = None

    def __init__(self, renderer: T_Renderer = None, logger: T_Logger | bool | None = None):
        if logger is True:
            # use default logger:
            logger = None

        def custom_catch_errors(app_name: str, func: AnyFunc) -> typing.Callable[..., str]:
            """Catches and logs errors in an action; also sets request.app_name"""

            # ^ THIS METHOD IS CALLED FOR EVERY ACTION DEFIFINED WITH @action

            # v METHOD BELOW IS CALLED ON EVERY ERROR

            @functools.wraps(func)
            def wrapper(*func_args: typing.Any, **func_kwargs: typing.Any) -> str | HTTPResponse:
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
                    err_code = 500
                    snapshot = get_error_snapshot()
                    if self.logger is not False:
                        # False - don't log
                        # None - default logger
                        (self.logger or default_error_logger)(snapshot)

                    ticket_uuid = error_logger.log(request.app_name, snapshot) or "unknown"
                    response.status = err_code

                    raise bottle.HTTPResponse(
                        body=custom_error_page(
                            err_code,
                            button_text=ticket_uuid,
                            href=f"/_dashboard/ticket/{ticket_uuid}",
                            traceback=tb.format_exc(),
                            err_type=type(e),
                            bare_exception=e,
                            renderer=getattr(patch_py4, "renderer", None),
                        ),
                        status=500,
                    )

            return wrapper

        # prevent duplicate enabling:
        if action.catch_errors.__qualname__ == "action.catch_errors":
            action.catch_errors = custom_catch_errors

        # allows swapping renderer on the fly with tools.set_renderer():
        patch_py4.renderer = renderer
        _logger = getattr(patch_py4, "logger", None) or logger
        patch_py4.logger = staticmethod(_logger) if _logger else None
