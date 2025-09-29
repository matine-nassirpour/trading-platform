import time
from datetime import datetime, timezone


def now_rfc3339_ms() -> str:
    """
    Current UTC time as RFC3339 string with millisecond precision.
    Example: '2025-09-29T14:12:45.123Z'
    """
    dt = datetime.now(tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def from_unix_s_to_rfc3339_ms(seconds: float) -> str:
    """
    Convert a UNIX timestamp (seconds since epoch) to RFC3339 with ms precision.
    Useful to format logging.LogRecord.created or any float UNIX timestamp.

    Args:
        seconds: UNIX epoch time in seconds (float allowed).
    """
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_unix_ms() -> int:
    """
    Current UNIX epoch time in milliseconds as int.
    """
    return int(time.time() * 1000)


def now_mono_ms() -> int:
    """
    Monotonic clock in milliseconds (not subject to system clock changes).
    Ideal for measuring durations/latencies and ordering events.
    """
    return time.monotonic_ns() // 1_000_000
