from __future__ import annotations

import logging
from typing import Any


def make_record(
    name: str = "t",
    level: int = logging.INFO,
    msg: str = "hello",
    *,
    extra: dict[str, Any] | None = None,
    exc_info: Any = None,
    created_ts: float | None = None,
    event: dict[str, Any] | None = None,
) -> logging.LogRecord:
    """
    Factory for consistent LogRecord instances used across tests.

    Args:
        name: logger name.
        level: logging level.
        msg: message string.
        extra: mapping of extra attributes to attach on the record.
        exc_info: standard logging exc_info triple.
        created_ts: if provided, overrides record.created (float seconds).
        event: if provided, attaches 'event' attribute (dict payload).

    Notes:
        - This function is backward compatible with previous calls that only
          set (name, level, msg, extra, exc_info).
        - For audit tests, use both `created_ts` and `event`.
    """
    logger = logging.getLogger(name)
    rec = logger.makeRecord(
        name=name, level=level, fn="x.py", lno=123, msg=msg, args=(), exc_info=exc_info
    )

    if created_ts is not None:
        rec.created = created_ts

    if extra:
        for k, v in extra.items():
            setattr(rec, k, v)

    if event is not None:
        setattr(rec, "event", event)

    return rec
