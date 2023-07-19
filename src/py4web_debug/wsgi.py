import typing

import py4web
from ombott import Ombott

from .core import patch_py4


# py4web.core.py:1716
def wsgi(**kwargs: typing.Any) -> Ombott:
    # action.catch_errors(app_name, func)
    original = py4web.core.wsgi

    patch_py4()
    return original(**kwargs)
