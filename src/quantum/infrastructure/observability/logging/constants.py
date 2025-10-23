import re
from typing import Final

from quantum.core.config.runtime.manager import ConfigManager

_AUDIT_EVENT_BASELINE_V1: Final = frozenset(
    {
        "order_submit",
        "order_ack",
        "order_fill",
        "order_reject",
        "killswitch_trigger",
        "reconciliation",
    }
)

# strict snake_case, low cardinality
_SAFE: Final = re.compile(r"^[a-z0-9_]+$")
# Generic version suffix (eg: _v1, _v2, _v10)
_VERSION_SUFFIX_RE: Final = re.compile(r"_v\d+$")


def _normalize(name: str) -> str:
    return (name or "").strip().lower()


def _strip_version_suffix(name: str) -> str:
    """Removes a generic version suffix (_v<digits>) if present."""
    n = _normalize(name)
    return _VERSION_SUFFIX_RE.sub("", n)


def _validate(name: str) -> None:
    if not _SAFE.match(name):
        raise ValueError(f"Invalid audit event name: {name!r}")


def get_audit_allowlist(version: str | None = None) -> set[str]:
    """
    Returns the allowlist of *bare* names (without suffixes), merged with QUANTUM_AUDIT_EVENTS (CSV).

    - Version suffixes (_v<digits>) are ignored on the allowlist side AND during the check.
    - The historical baseline (V1) is used **for all versions** to avoid
    false negatives during a version upgrade (backward compatible).
    """
    logging_settings = ConfigManager.load_logging()

    # Stable, version-independent baseline
    baseline = set(_AUDIT_EVENT_BASELINE_V1)

    # Extras from the env (CSV). We clean and remove any suffixes.
    extra_csv = (logging_settings.quantum_audit_events or "").strip()
    if extra_csv:
        for raw in extra_csv.split(","):
            n = _strip_version_suffix(raw)
            if n:
                _validate(n)
                baseline.add(n)

    return baseline


def is_audit_event(event_name: str, version: str | None = None) -> bool:
    """
    Checks if `event_name` (with or without a suffix, e.g., 'order_submit' or 'order_submit_v2')
    is part of the effective allowlist.

    - `version` is retained for signature compatibility, but detection is intentionally
    **version-agnostic**: the *bare* name is compared against the allowlist.
    """
    n = _strip_version_suffix(event_name)
    try:
        _validate(n)
    except ValueError:
        return False
    return n in get_audit_allowlist(version)
