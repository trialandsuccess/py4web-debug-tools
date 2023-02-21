import os


def is_debug():
    return str(os.getenv("PY4WEB_DEBUG_MODE")) == "1"
