import py4web
from .core import patch_py4


# py4web.core.py:1716
def wsgi(**kwargs):
    # action.catch_errors(app_name, func)
    original = py4web.core.wsgi

    patch_py4()
    return original(**kwargs)
