import ast
import inspect
import json
import sys
import traceback
import typing
from types import FrameType

import pydal.objects
from configurablejson import ConfigurableJsonEncoder, JSONRule
from py4web import response

from .env import is_debug


class PossiblyAsDict(typing.Protocol):
    def as_dict(self) -> dict[str, typing.Any]: ...

    def asdict(self) -> dict[str, typing.Any]: ...

    def _asdict(self) -> dict[str, typing.Any]: ...

    def _as_dict(self) -> dict[str, typing.Any]: ...

    def to_dict(self) -> dict[str, typing.Any]: ...

    def todict(self) -> dict[str, typing.Any]: ...

    def _todict(self) -> dict[str, typing.Any]: ...

    def _to_dict(self) -> dict[str, typing.Any]: ...

    def __json__(self) -> dict[str, typing.Any]: ...

    def as_list(self) -> list[typing.Any]: ...


class DDJsonEncoder(ConfigurableJsonEncoder):
    @staticmethod
    def _default(o: PossiblyAsDict) -> dict[str, typing.Any] | list[typing.Any] | str:
        if hasattr(o, "as_list"):
            # note: prefer as_list now as not every Rows may have an id (= default key of as_dict)
            return o.as_list()
        # more as list stuff?

        if hasattr(o, "as_dict"):
            return o.as_dict()
        elif hasattr(o, "asdict"):
            return o.asdict()
        elif hasattr(o, "_asdict"):
            return o._asdict()
        elif hasattr(o, "_as_dict"):
            return o._as_dict()
        elif hasattr(o, "to_dict"):
            return o.to_dict()
        elif hasattr(o, "todict"):
            return o.todict()
        elif hasattr(o, "_todict"):
            return o._todict()
        elif hasattr(o, "_to_dict"):
            return o._to_dict()
        elif hasattr(o, "__json__"):
            return o.__json__()

        return str(o)

    @staticmethod
    def is_probably_namedtuple(o: typing.Any) -> bool:
        """
        Try to guess if 'o' is a Named Tuple or something else.
        """
        return isinstance(o, tuple) and hasattr(o, "_fields")

    def rules(self, o: typing.Any, with_default: bool = True) -> JSONRule:
        """
        Custom rules for the DD json: set to list and namedtuple to dict
        # NOTE: with_default is (probably) false anyway!!!!
        """

        _type = typing.NamedTuple if self.is_probably_namedtuple(o) else type(o)

        rules: dict[type, JSONRule] = {
            # convert set to list
            set: JSONRule(preprocess=lambda o: list(o)),
            # convert namedtuple to dict
            typing.NamedTuple: JSONRule(preprocess=self._default),
            pydal.objects.Row: JSONRule(preprocess=lambda row: row.as_dict()),
            pydal.objects.Rows: JSONRule(preprocess=lambda row: row.as_list()),
        }

        if rule := rules.get(typing.cast(type, _type)):
            return rule
        elif rule is None and with_default:
            return JSONRule(transform=self._default)
        else:
            # empty rule:
            return JSONRule()


def dump(data: typing.Iterable[typing.Any], with_headers: bool = True) -> str:
    """
    Helper to json dump some data with custom converter and headers
    """
    if with_headers:
        response.headers["Content-Type"] = "application/json"

    return json.dumps(data, indent=2, cls=DDJsonEncoder)
    # return json.dumps(data, indent=2, default=DDJsonEncoder._default)


class DumpDieError(Exception):
    """
    Custom Exception used to catch dd() in py4web error page -> regular output
    """

    pass


class FancyDumpDieError(Exception):
    """
    Custom Exception used to catch dd() in py4web error page -> styled output
    """

    pass


class ApiDumpDieError(Exception):
    """
    Custom Exception used to catch dd() in py4web error page -> JSON only output
    """

    pass


def dd(*data: typing.Any, fancy: bool = True, api: bool = False) -> None:
    """
    Dump and Die:
    Show args as JSON an halt the rest of the request
    (useful for debugging fifty levels deep in some helper method)

    """
    if len(data) == 1:
        data = data[0]

    if not is_debug():
        # simpler:
        print("dd |", data, file=sys.stderr)
        return

    # if is_debug: more complex error
    _json = dump(data)
    if api:
        # todo: detect automatically?
        raise ApiDumpDieError(_json)
    elif fancy:
        raise FancyDumpDieError(_json)
    else:
        raise DumpDieError(_json)


T = typing.TypeVar("T")


def _extract_dbg_variable_name(frame: FrameType) -> str:
    # Read the full source of the caller file
    with open(frame.f_code.co_filename, "r", encoding="utf-8") as f:
        source_code = f.readlines()

    # Extract the relevant lines (handle multiline statements)
    full_source = ""
    line_number = frame.f_lineno - 1
    while line_number < len(source_code):
        full_source += source_code[line_number].strip()
        if full_source.count("(") == full_source.count(")"):  # Ensure all parentheses are closed
            break
        line_number += 1

    # Parse the AST
    tree = ast.parse(full_source)

    # Find the relevant call in the AST
    var_name = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            while isinstance(call, ast.Call):  # Handle nested function calls
                if hasattr(call.func, "id") and call.func.id == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                elif isinstance(call.func, ast.Attribute) and call.func.attr == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                call = call.args[0] if call.args else None
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            while isinstance(call, ast.Call):  # Handle assignments with nested calls
                if hasattr(call.func, "id") and call.func.id == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                elif isinstance(call.func, ast.Attribute) and call.func.attr == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                call = call.args[0] if call.args else None
        elif isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
            call = node.value
            while isinstance(call, ast.Call):  # Handle return dbg(x)
                if hasattr(call.func, "id") and call.func.id == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                elif isinstance(call.func, ast.Attribute) and call.func.attr == "dbg":
                    var_name = ast.unparse(call.args[0])
                    break
                call = call.args[0] if call.args else None
        elif isinstance(node, ast.keyword) and isinstance(node.value, ast.Call):
            # Handle function keyword arguments like some_func(arg=dbg("arg"))
            call = node.value
            if hasattr(call.func, "id") and call.func.id == "dbg":
                var_name = ast.unparse(call.args[0])
                break
            elif isinstance(call.func, ast.Attribute) and call.func.attr == "dbg":
                var_name = ast.unparse(call.args[0])
                break

    return var_name


def extract_dbg_variable_name(frame: FrameType) -> typing.Optional[str]:
    """
    Extracts the variable name passed to dbg() from the source code.
    Handles multiline statements, assignments, function arguments, and return values.
    """
    try:
        return _extract_dbg_variable_name(frame)
    except Exception:
        return None


def dbg(value: T) -> T:
    """
    Improved Rust-like dbg function that captures variable names even in assignments,
    namespaced calls, and nested function calls.
    Handles multiline calls, function arguments, and return statements.

    Examples:

        ```
        def handle(_):
            ...

        def my_decorator(fn): return fn

        @my_decorator
        def some_func(arg):
            return dbg("hello")


        dbg('hi')
        y = dbg('hi')
        py4web_debug.dbg('hi')
        z = py4web_debug.dbg('hi')

        handle(dbg('hi'))
        handle(py4web_debug.dbg('hi'))

        some_long_expression = " 3 + 123"

        handle(
            dbg(
                (
                    some_long_expression +
                    some_long_expression
                )
            )
        )

        some_func(arg=dbg("arg1"))
        ```
    """
    value_type = type(value).__name__

    # Get the caller's frame
    frame = inspect.currentframe().f_back
    frame_info = inspect.getframeinfo(frame)
    file_name = frame_info.filename.split("/")[-1]
    line_number = frame_info.lineno

    var_name = extract_dbg_variable_name(frame) or "?"

    print(f"[{file_name}:{line_number}] {value_type}({var_name}) = {value}", file=sys.stderr)
    return value
