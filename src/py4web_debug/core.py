# Transforms janky 'internals' into easy to work with tool
import os
import typing
from dataclasses import dataclass

from py4web import DAL as P4WDAL

from .debugbar import DebugBar, DummyDebugBar
from .env import is_debug
from .internals import T_Logger, T_Renderer, patch_py4


@dataclass
class ErrorpageSettings:
    enabled: bool


@dataclass
class DebugbarSettings:
    enabled: bool


@dataclass
class InternalConfig:
    errorpage: ErrorpageSettings
    debugbar: DebugbarSettings


class DebugTools:
    # by default, it is not enabled! This is so you can still import it on production,
    # but don't actually show any debug info. enable(on_off) can be called with e.g. an ENV variable
    enabled = False
    db: P4WDAL
    debug_bar = DummyDebugBar()
    IS_DEBUG: bool = is_debug()

    config: InternalConfig

    def enable(
        self,
        # general settings:
        db: P4WDAL = None,
        enabled: bool | None = None,  # OVERWRITES errorpage_enabled and debugbar_enabled
        set_env_var: bool = True,
        # error screen settings:
        errorpage_enabled: bool = None,  # value of 'enabled' is used by default
        errorpage_renderer: T_Renderer = None,
        # can be set to False to disable (e.g. when using PY4WEB_ERRORLOG: ":stderr"):
        error_logger: T_Logger | typing.Literal[False] | None = None,
        # debugbar settings:
        debugbar_enabled: bool = None,  # value of 'enabled' is used by default
        debugbar_fancy_rendering: bool = True,
        debugbar_style: typing.Literal["bootstrap"] = "bootstrap",
        debugbar_slow_threshold_ms: int = 10,
    ) -> None:
        """
        By default, on_off looks at PY4WEB_DEBUG_MODE in the env
        """
        if enabled is None:
            enabled = is_debug()

        self.db = db
        self.enabled = enabled

        self.IS_DEBUG = enabled

        self.config = InternalConfig(
            errorpage=ErrorpageSettings(enabled=errorpage_enabled in {True, None}),
            # todo: more
            debugbar=DebugbarSettings(enabled=debugbar_enabled in {True, None}),
            # todo: more
        )

        if enabled:
            if self.config.errorpage.enabled:
                patch_py4(errorpage_renderer, error_logger)

            if self.config.debugbar.enabled:
                if not db:
                    raise ValueError("`db` variable should be provided when using the debug bar!")

                self.debug_bar = DebugBar(
                    db,
                    debugbar_fancy_rendering,
                    debugbar_style,
                    debugbar_slow_threshold_ms,
                )

            if set_env_var:
                # will change the result of is_debug (hopefully)
                os.environ["PY4WEB_DEBUG_MODE"] = "1"
        else:
            self.debug_bar = DummyDebugBar()

    def set_renderer(self, cb: T_Renderer) -> None:
        # swap the errorpage_renderer
        if not (self.enabled and self.config.errorpage.enabled):
            # do nothing
            return

        patch_py4.renderer = cb


tools = DebugTools()

__all__ = ["tools", "patch_py4"]
