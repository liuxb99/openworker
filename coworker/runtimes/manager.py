"""Runtime selection primitives.

Only the native runtime is available in H1. The manager centralizes names and
availability so later Harness work has one switch point instead of scattering
string checks through server/session code.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class RuntimeKind(str, Enum):
    NATIVE = "native"
    HARNESS = "harness"


DEFAULT_RUNTIME = RuntimeKind.NATIVE


class RuntimeUnavailableError(ValueError):
    """Raised when a known runtime is requested before it is available."""


def parse_runtime(value: Optional[str]) -> RuntimeKind:
    """Parse a configured runtime name; missing values retain native default."""
    if value is None or not str(value).strip():
        return DEFAULT_RUNTIME
    try:
        return RuntimeKind(str(value).strip().lower())
    except ValueError as exc:
        choices = ", ".join(item.value for item in RuntimeKind)
        raise ValueError(f"unknown agent runtime {value!r}; expected one of: {choices}") from exc


def require_available(kind: RuntimeKind) -> RuntimeKind:
    """Fail closed for runtimes not implemented in the current build."""
    if kind is not RuntimeKind.NATIVE:
        raise RuntimeUnavailableError(
            f"agent runtime {kind.value!r} is not available in this build"
        )
    return kind


def select_runtime(value: Optional[str] = None) -> RuntimeKind:
    """Resolve and validate the runtime selected for a session."""
    return require_available(parse_runtime(value))


__all__ = [
    "DEFAULT_RUNTIME",
    "RuntimeKind",
    "RuntimeUnavailableError",
    "parse_runtime",
    "require_available",
    "select_runtime",
]
