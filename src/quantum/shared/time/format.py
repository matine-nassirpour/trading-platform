from __future__ import annotations

import re
import time
from datetime import datetime, timezone

# RFC3339 UTC with EXACT milliseconds and 'Z' suffix
_RFC3339_MS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Current time                                                                │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def now_rfc3339_ms() -> str:
    """Current UTC time as RFC3339 string with millisecond precision."""
    dt = datetime.now(tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_epoch_ms() -> int:
    """Current UTC epoch time in milliseconds."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1_000)


def now_mono_ms() -> int:
    """Monotonic timestamp in milliseconds (system-clock drift safe)."""
    return time.monotonic_ns() // 1_000_000


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Conversions                                                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def to_rfc3339_ms(seconds: float) -> str:
    """Convert UNIX timestamp (seconds) to RFC3339 with ms precision."""
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_rfc3339_ms(value: str) -> datetime:
    """Parse RFC3339 timestamp (ms precision) to UTC datetime."""
    if not _RFC3339_MS.match(value):
        raise ValueError(
            f"Invalid RFC3339 timestamp (expected ms precision + 'Z' suffix): {value!r}"
        )
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.replace(tzinfo=timezone.utc)


def to_unix_s(value: datetime) -> float:
    """Convert UTC datetime to UNIX timestamp (seconds)."""
    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware (UTC)")
    return value.timestamp()


def to_unix_ms(value: datetime) -> int:
    """Convert UTC datetime to UNIX timestamp (milliseconds)."""
    return int(to_unix_s(value) * 1_000)


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Validation helpers                                                          │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def is_rfc3339_ms(value: str) -> bool:
    """Returns True if value matches RFC3339 UTC with millisecond precision."""
    return bool(_RFC3339_MS.match(value))


def require_rfc3339_ms(value: str) -> str:
    """Validate and return value if matches RFC3339 format."""
    if not is_rfc3339_ms(value):
        raise ValueError(
            "timestamp must be RFC3339 with millisecond precision and 'Z' suffix"
        )
    return value
