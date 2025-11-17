import re

from typing import Final

from quantum.infrastructure.config.runtime.manager import ConfigManager

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
_AUDIT_EVENT_BASELINE_V1: Final[frozenset[str]] = frozenset(
    {
        "order_submit",
        "order_ack",
        "order_fill",
        "order_reject",
        "killswitch_trigger",
        "reconciliation",
    }
)

_SAFE_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_]+$")
_VERSION_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r"_v\d+$")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _normalize_name(name: str) -> str:
    """Normalize event name to lowercase and strip whitespace."""
    return (name or "").strip().lower()


def _strip_version_suffix(name: str) -> str:
    """Remove trailing version suffix (e.g., _v1, _v2)."""
    normalized = _normalize_name(name)
    return _VERSION_SUFFIX_RE.sub("", normalized)


def _validate_name(name: str) -> None:
    """
    Validate that a given audit event name follows snake_case syntax
    and contains only lowercase alphanumerics or underscores.
    """
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(f"Invalid audit event name: {name!r}")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def get_audit_allowlist(version: str | None = None) -> set[str]:
    """
    Compute the effective allowlist of audit event *base names*
    (without version suffixes) for the given environment.

    Behavior:
        - Starts from a stable, version-agnostic baseline (V1).
        - Merges optional CSV entries from QUANTUM_AUDIT_EVENTS.
        - Strips version suffixes and validates all entries.
        - Returns a normalized `set[str]` of allowed event names.

    Returns:
        A set of normalized event names allowed in the current environment.
    """
    logging_settings = ConfigManager.load_logging()

    # Stable baseline
    baseline = set(_AUDIT_EVENT_BASELINE_V1)

    # Merge environment extras (CSV)
    extra_csv = (logging_settings.quantum_audit_events or "").strip()
    if extra_csv:
        for raw in extra_csv.split(","):
            name = _strip_version_suffix(raw)
            if not name:
                continue
            _validate_name(name)
            baseline.add(name)

    return baseline


def is_audit_event(event_name: str, version: str | None = None) -> bool:
    """
    Check if an event name (with or without version suffix) is
    part of the current audit allowlist.

    Example
    -------
    >>> is_audit_event("order_submit_v2")
    True
    """
    name = _strip_version_suffix(event_name)
    try:
        _validate_name(name)
    except ValueError:
        return False
    return name in get_audit_allowlist(version)
