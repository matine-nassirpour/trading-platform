from __future__ import annotations

from datetime import UTC, datetime


def to_timestamp(dt: datetime) -> float:
    """
    Return a UNIX timestamp (float seconds) from an aware or naïve datetime.
    - Naïve datetimes are assumed to be in UTC.
    - Always returns a float representing seconds since the epoch (UTC).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.timestamp()
