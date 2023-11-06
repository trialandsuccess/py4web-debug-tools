from typing import TypedDict


class SystemInfo(TypedDict):
    machine: str
    node: str
    platform: str
    processor: str
    python_branch: str
    python_build: tuple[str, str]
    python_compiler: str
    python_implementation: str
    python_revision: str
    python_version: str
    python_version_tuple: tuple[str, str, str]
    release: str
    system: str
    uname: tuple[str, str, str, str, str]


class OsEnviron(TypedDict):
    SHELL: str
    SESSION_MANAGER: str
    QT_ACCESSIBILITY: str
    # ... (other key-value pairs)


class StackFrame(TypedDict):
    file: str
    func: str
    lnum: int
    code: list[str]


class Traceback(TypedDict):
    file: str
    func: str
    lnum: int
    code: list[str]


class ErrorSnapshot(TypedDict):
    timestamp: str
    python_version: str
    platform_info: SystemInfo
    os_environ: OsEnviron
    traceback: str
    exception_type: str
    exception_value: str
    stackframes: list[StackFrame]
