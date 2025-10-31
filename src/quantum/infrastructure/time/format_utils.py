from __future__ import annotations

import time
from datetime import datetime, timezone


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Current time                                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Conversions                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def to_rfc3339_ms(seconds: float) -> str:
    """Convert UNIX timestamp (seconds) to RFC3339 with ms precision."""
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
