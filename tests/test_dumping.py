from types import SimpleNamespace

import pytest
from dotmap import DotMap
from pytest import MonkeyPatch

from src.py4web_debug.dumping import DDJsonEncoder, DumpDieError, DumpSerializationError, dd, dump


def _sample_dotmap() -> DotMap:
    data = DotMap()
    data.a = 1
    data.b.c = "nested"
    return data


def test_dump_handles_dotmap():
    # dump() should serialize a DotMap without crashing.
    result = dump(_sample_dotmap(), with_headers=False)

    assert '"a": 1' in result
    assert '"c": "nested"' in result


def test_dd_handles_dotmap(monkeypatch: MonkeyPatch):
    # dd() should not crash on a DotMap; in debug mode it raises a DumpDieError
    # (by design) instead of letting json serialization blow up.
    monkeypatch.setenv("PY4WEB_DEBUG_MODE", "1")

    try:
        dd(_sample_dotmap(), fancy=False)
    except DumpDieError as e:
        assert '"a": 1' in str(e)
    else:
        raise AssertionError("dd() should raise DumpDieError in debug mode")


def test_default_crashes_on_bare_dotmap():
    """
    DotMap's __getattr__ returns an empty DotMap for ANY missing attribute
    instead of raising AttributeError, so hasattr(dotmap, "as_list") is
    always True even though `as_list` isn't a real method on it.

    Note: dump()/dd() never hit this for a *bare* DotMap in practice, because
    DotMap is a dict subclass and gets recognized (and recursed into) by
    configurablejson's encoder before _default() is ever called - see
    test_dump_handles_dotmap above, which passes fine. This test instead
    calls DDJsonEncoder._default() directly, to pin the underlying flaw that
    both this and the TypeDAL-model-class crash below share.

    FAILS until DDJsonEncoder._default() is fixed:
    TypeError: 'DotMap' object is not callable
    """
    d = DotMap({"label": "Dashboard"})

    DDJsonEncoder._default(d)


class _TableMetaLike(type):
    """
    Reproduces TypeDAL's `TableMeta.__getattr__`: for an unbound model class,
    any attribute that isn't a real column falls through to `return None`
    instead of raising AttributeError (see typedal/tables.py TableMeta.__getattr__).
    """

    def __getattr__(cls, name: str) -> None:
        return None


class Offering(metaclass=_TableMetaLike):
    """Stand-in for a real TypeDAL model class, e.g. used as menu["model"]."""


def test_dump_reproduces_as_list_crash_on_model_class_value():
    """
    Real-world crash reproduction (whitelabel AdminMenuFixture):
    admin nav menu entries are plain dicts that carry a `"model"` key holding
    the *model class itself* (e.g. `Offering`, not an instance). Wrapping such
    an entry in a DotMap (for dot-access in templates) doesn't cause this —
    a plain dict crashes identically, see test below.

    FAILS until DDJsonEncoder._default() is fixed: it does
    `if hasattr(o, "as_list"): o.as_list()` without checking it's callable.
    TypeDAL's TableMeta.__getattr__ returns None for unknown attributes on a
    model class instead of raising AttributeError, so hasattr() lies and
    `o.as_list()` becomes `None()`. Matches production traceback exactly:
    dumping.py:42 in _default -> TypeError: 'NoneType' object is not callable.
    """
    entry = DotMap({"label": "Aanbod beheren", "icon": "fas fa-masks-theater", "model": Offering})

    dump(entry, with_headers=False)


def test_dump_reproduces_as_list_crash_without_dotmap():
    # Same crash with a plain dict: DotMap is incidental, not the cause.
    entry1 = {"label": "Aanbod beheren", "model": Offering}
    dump(entry1, with_headers=False)

    entry2 = SimpleNamespace(label="Aanbod beheren", model=Offering)
    dump(entry2, with_headers=False)


def test_dump_wraps_unexpected_errors_with_context():
    """
    Force *some other* JSON-serialization failure (a plain circular reference,
    nothing to do with DotMap/permissive __getattr__) to prove dump() wraps
    whatever goes wrong with a nicer, actionable error instead of leaking a
    bare exception from deep inside json.dumps()/DDJsonEncoder.
    """
    circular: dict = {}
    circular["self"] = circular

    with pytest.raises(DumpSerializationError) as exc_info:
        dump(circular, with_headers=False)

    err = exc_info.value
    assert "could not JSON-serialize" in str(err)
    assert "dict" in str(err)  # names the top-level type that was being dumped
    assert isinstance(err.__cause__, ValueError)  # original error is preserved/chained
    assert "circular" in str(err.__cause__).lower()
