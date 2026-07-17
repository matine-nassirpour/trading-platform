import re

from collections.abc import Iterable
from typing import Final

_SAFE_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_]+$")
_VERSION_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r"_v\d+$")


# --- Internal Helpers
def _normalize_event_name(name: str) -> str:
    """
    Normalize an audit event name:
    - strip whitespace
    - lowercase
    - strip trailing version suffix (_v1, _v2, ...)
    """
    if not isinstance(name, str):
        raise TypeError(f"event name must be a string, got {type(name).__name__}")

    name = name.strip().lower()
    name = _VERSION_SUFFIX_RE.sub("", name)
    return name


def _validate_event_name(name: str) -> None:
    """
    Validate that an audit event name is syntactically correct:
    - snake_case
    - lowercase alphanumerics + underscores
    """
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(f"Invalid audit event name: {name!r}")


# --- Public API
def normalize_allowlist(events: Iterable[str]) -> frozenset[str]:
    """Normalize & validate a set/list of event names before using them."""
    normalized: set[str] = set()

    for raw in events:
        name = _normalize_event_name(raw)
        _validate_event_name(name)
        normalized.add(name)

    return frozenset(normalized)


def is_allowed_event(name: str, allowlist: frozenset[str]) -> bool:
    """
    Lightweight check to determine if an event name (with or without version suffix)
    belongs to a provided allowlist.

    Used primarily by AuditEventFilter.
    """
    try:
        name = _normalize_event_name(name)
        _validate_event_name(name)
    except Exception:
        return False

    return name in allowlist
