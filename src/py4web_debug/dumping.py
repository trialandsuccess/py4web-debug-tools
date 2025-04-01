import ast
import json
import sys
import traceback
import typing

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


def dbg(value: T) -> T:
    """
    Helper inspired by Rust's `dbg!`.

    Prints out the file, line, variable name, type and value.
    Also returns the original value.
    """
    value_type = type(value).__name__

    frame = traceback.extract_stack()[-2]  # Get caller frame info
    file_name = frame.filename.split("/")[-1]
    line_number = frame.lineno

    try:
        with open(frame.filename, "r") as f:
            source_code = f.readlines()

        line = source_code[line_number - 1].strip()
        tree = ast.parse(line)

        var_name = None
        if isinstance(tree, ast.Module) and isinstance(tree.body[0], ast.Expr):
            call = tree.body[0].value
            if isinstance(call, ast.Call) and call.func.id == "dbg":
                var_name = ast.unparse(call.args[0])  # Extract the first argument as a string

    except Exception:
        var_name = "?"

    print(f"[{file_name}:{line_number}] {value_type}({var_name}) = {value}", file=sys.stderr)

    return value
