import os
import re
from typing import Final

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

_SAFE: Final = re.compile(r"^[a-z0-9_]+$")  # strict snake_case, low cardinality


def _normalize(name: str) -> str:
    return name.strip().lower()


def _validate(name: str) -> None:
    if not _SAFE.match(name):
        raise ValueError(f"Invalid audit event name: {name!r}")


def get_audit_allowlist(version: str | None = None) -> set[str]:
    """
    Returns the allowlist of *bare* event names (no version suffix),
    merged with QUANTUM_AUDIT_EVENTS (CSV). Version defaults to
    QUANTUM_AUDIT_EVENTS_VERSION or "v1".
    """
    env_version = os.getenv("QUANTUM_AUDIT_EVENTS_VERSION", "v1").strip().lower()
    ver = version or env_version
    if ver != "v1":
        # Future-proof: unknown versions return empty baseline.
        baseline = set()
    else:
        baseline = set(_AUDIT_EVENT_BASELINE_V1)

    extra_csv = os.getenv("QUANTUM_AUDIT_EVENTS", "").strip()
    extras = set()
    if extra_csv:
        for raw in extra_csv.split(","):
            n = _normalize(raw)
            if n:
                _validate(n)
                extras.add(n)

    return baseline | extras


def is_audit_event(event_name: str, version: str | None = None) -> bool:
    """
    Accepts both "bare" (e.g., 'order_submit') and suffixed (e.g., 'order_submit_v1').
    """
    n = _normalize(event_name)
    if n.endswith("_v1"):
        n = n[:-3]
    try:
        _validate(n)
    except ValueError:
        return False
    return n in get_audit_allowlist(version)
