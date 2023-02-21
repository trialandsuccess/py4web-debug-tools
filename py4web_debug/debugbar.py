import os
import typing
import warnings
from collections import Counter

import yatl
from py4web import request
from py4web.core import Template, Fixture
from yatl import XML

from .env import is_debug
from .dumping import dump


def _fmt_callframe(cf):
    # 0: frame
    # 1: file
    # 2: lineno
    # 3: function
    # 4: context
    filename = cf[1].split("/")[-1]
    function = cf[3]
    return f"{filename}:{function}"


def catch(*context, levels=3, _from=1):
    """
    Log usages of this method
    """
    _ = "You should only use catch() while debugging!!!!"

    if not is_debug():
        warnings.warn(_)
        return  # just do nothing (but warn)
        # raise ValueError(_)

    import inspect

    curframe = inspect.currentframe()
    calframes = inspect.getouterframes(curframe, 4)[_from: levels + 1]

    cfl = [_fmt_callframe(cf) for cf in calframes]
    print("catch | ", *cfl, "|", *context)

    c = getattr(request, "_catch", [])
    c.append(
        {
            "callframes": cfl,
            "context": context,
        }
    )
    setattr(request, "_catch", c)


def _debugbar(data, template="templates/debugbar.html", fancy=True):
    fname = os.path.join(os.path.dirname(__file__), template)

    if not data.get("queries"):
        data["queries"] = []

    if not data.get("duplicate_queries"):
        data["duplicate_queries"] = []

    if not data.get("slow_queries"):
        data["slow_queries"] = []

    if not data.get("catch"):
        data["catch"] = []

    if not data.get("json_context"):
        data["json_context"] = []

    data["fancy"] = fancy

    return yatl.render(
        filename=fname,
        context={"BEAUTIFY": yatl.BEAUTIFY, **data},
        delimiters="[[ ]]",
    )


def render_debugbar(*contexts, fancy=True):
    """
    Contexts should be:
    1. debug data (filled in the Debug Bar Fixture)
    2. on_success context, after rendering (so output = html), including other info such as fixtures
    3. context['output'] from before it is rendered by the template
    """

    debug_data, _, input_data = contexts
    return _debugbar(debug_data, fancy=fancy) + "</html>"


def debugbar_template(fixture: Fixture, debug_data: dict, fancy=True):
    """
    debug_data is reset and filled every request
    """

    if not hasattr(Template, "_on_success"):
        # DON'T overwrite existing _on_success because that will lead to recursion...
        Template._on_success = Template.on_success

    def _on_request(self, context: dict):
        if not (context and context.get("output")):
            # do nothing
            return

        if isinstance(context.get("output"), dict):
            pre_render_output = context["output"].copy()
        else:
            # no data?
            pre_render_output = {}

        Template._on_success(self, context)

        # only replace actual templates (= end in /html)
        if (output := context["output"]) and isinstance(output, str):
            context["output"] = output.replace(
                "</html>",
                render_debugbar(debug_data, context, pre_render_output, fancy=fancy),
            )

    def on_success(self, context: dict):
        try:
            _on_request(self, context)
        finally:
            # after output has been rendered, reset to original on_success (so next request will reset):
            Template.on_success = Template._on_success

    Template.on_success = on_success


T = typing.TypeVar("T")


def _prune_long_values(value: T) -> T | str:
    """
    Find the end values in nested dicts and lists and prune them if they are too long,
    Usually (tm) returns the same type as the input (except when the input is long bytes)
    """
    # mut value
    if isinstance(value, list):
        for idx, item in enumerate(value):
            value[idx] = _prune_long_values(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            value[key] = _prune_long_values(item)
    elif isinstance(value, str | bytes) and len(value) > 50:
        return "[pruned due to length]"

    return value


def convert_for_debugbar(value):
    """
    Returns: a dict or list that can be converted to json
    """
    # deprecated: as dict is now managed by dump()
    # if hasattr(value, "as_dict"):
    #     value = value.as_dict()
    #
    # elif hasattr(value, "_asdict"):
    #     value = value._asdict()

    value = _prune_long_values(value)
    return value


class DummyDebugBar(Fixture):
    ...


class DebugBar(Fixture):
    queries = []  # mutable but DONT OVERWRITE !!!
    debug_data = {}  # mutable but DON'T OVERWRITE!!

    def __init__(
        self,
        db,
        fancy_rendering: bool,
        bar_style: typing.Literal["bootstrap"],
        slow_threshold_ms: int,
    ):
        self.__prerequisites__ = [db]
        self.db = db
        self.fancy = fancy_rendering
        self.style = bar_style
        self.threshold_ms = slow_threshold_ms

    def _find_duplicate_queries(self, timings):
        """
        Returns: a dict of queries (+ count as value) that are executed more than once
        """
        counts = Counter(query for query, _ in timings)

        return {query: count for query, count in counts.items() if count > 1}

    def _find_slow_queries(self, timings: list[tuple[str, float]], threshold_ms: int):
        """
        Returns: a list of queries that took longer than threshold_ms
        """
        return [
            {q: f"{round(t * 1000, 5)}ms"}
            for q, t in timings
            if t > threshold_ms / 1000
        ]

    def on_request(self, context):
        db = self.db
        # these two are scoped to the request
        self.queries.clear()  # DON'T OVERWRITE WITH = [] !!!
        self.debug_data.clear()  # idem
        db._timings.clear()

        self.debug_data["queries"] = db._timings
        setattr(request, "_catch", [])

        # empty before debug_pydal adds new queries
        # patch the Template.on_success:
        debugbar_template(self, self.debug_data, fancy=self.fancy)

    def filter_context(self, input_data: dict):
        """
        Returns: a dict with all keys that are not in __ignored and it's values shortened (nested long values are pruned)
        """
        if not input_data or not isinstance(input_data, dict):
            return {}

        __ignored = input_data.get("__ignore", [])

        # remove common helper methods etc.
        return {
            k: convert_for_debugbar(v)
            for k, v in input_data.items()
            if k not in __ignored
        }

    def on_success(self, context):
        self.debug_data["duplicate_queries"] = self._find_duplicate_queries(
            self.debug_data["queries"]
        )
        self.debug_data["slow_queries"] = self._find_slow_queries(
            self.debug_data["queries"],
            threshold_ms=self.threshold_ms
        )

        try:
            json_context = dump(
                self.filter_context(context["output"]), with_headers=False
            )
        except:
            json_context = "(Something went wrong)"

        self.debug_data["json_context"] = XML(json_context)

        self.debug_data["catch"] = getattr(request, "_catch", [])
