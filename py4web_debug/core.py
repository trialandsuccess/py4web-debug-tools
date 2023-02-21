# Transforms janky 'internals' into easy to work with tool
import os

from py4web import DAL as P4WDAL

from .debugbar import DummyDebugBar, DebugBar
from .internals import patch_py4


class DebugTools:
    # by default, it is not enabled! This is so you can still import it on production,
    # but don't actually show any debug info. enable(on_off) can be called with e.g. an ENV variable
    enabled = False
    db: P4WDAL
    debug_bar = DummyDebugBar()

    def enable(self, db: P4WDAL, enabled: bool = None, fancy_rendering=True):
        """
        By default, on_off looks at PY4WEB_DEBUG_MODE in the env

        @todo: debugbar style (bootstrap/default, bulma, ...)
        """
        if enabled is None:
            enabled = os.getenv("PY4WEB_DEBUG_MODE", False)

        self.db = db
        self.enabled = enabled

        if enabled:
            patch_py4()
            self.debug_bar = DebugBar(db, fancy_rendering)

            # will change the result of is_debug (hopefully)
            os.environ['PY4WEB_DEBUG_MODE'] = "1"
        else:
            self.debug_bar = DummyDebugBar()


tools = DebugTools()
