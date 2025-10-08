from __future__ import annotations

from datetime import datetime, timezone


def to_timestamp(dt: datetime) -> float:
    """
    Return a UNIX timestamp (float seconds) from an aware or naïve datetime.
    - Naïve datetimes are assumed to be in UTC.
    - Always returns a float representing seconds since the epoch (UTC).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.timestamp()
