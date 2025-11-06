from __future__ import annotations

import logging

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, cast

from tests.support.types import NumberLike


class ListHandler(logging.Handler):
    """In-memory handler capturing LogRecord instances for assertions."""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def capture_logger(name: str, level: int = logging.DEBUG):
    """
    Temporarily attach a memory handler to `name`. Yields a list of LogRecords.
    """
    logger = logging.getLogger(name)
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler(level=level)
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(min(old_level or level, level))
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def counter_value(c: Any) -> float:
    """
    Safe extraction of a prometheus_client Counter value.

    Returns:
        float: current value if available, otherwise -1.0 (keeps tests resilient
        if internals differ or the object is a stub).
    """
    maybe_get = getattr(getattr(c, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], NumberLike], maybe_get)())
    except Exception:
        return -1.0


@contextmanager
def propagate_logger(name: str):
    """
    Temporarily set logger.propagate=True for caplog/root capture.
    """
    logger = logging.getLogger(name)
    old = logger.propagate
    try:
        logger.propagate = True
        yield
    finally:
        logger.propagate = old
