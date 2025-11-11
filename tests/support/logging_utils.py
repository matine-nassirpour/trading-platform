from __future__ import annotations

import logging
import os
import threading

from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any, cast

from tests.support.types import NumberLike


class ListHandler(logging.Handler):
    """In-memory handler capturing LogRecord instances for assertions."""

    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def capture_logger(
    name: str, level: int = logging.DEBUG
) -> Generator[list[logging.LogRecord]]:
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
def propagate_logger(name: str) -> Generator[None]:
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


def _iter_all_loggers() -> list[logging.Logger]:
    """
    Return all known loggers including root and children registered in the manager.

    This helps aggressively close/flush every handler that may have been added
    by the code under test, avoiding FD leaks across tests.
    """
    # Start with root
    loggers: list[logging.Logger] = [logging.getLogger()]
    # Add any named loggers present in the registry
    for name in list(logging.root.manager.loggerDict.keys()):
        try:
            loggers.append(logging.getLogger(name))
        except Exception:
            # Defensive: ignore malformed entries
            continue
    return loggers


def close_all_handlers() -> None:
    """
    Cleanly flush/close and detach all handlers of all known loggers.

    Thread-safe: ensures that only one cleanup operation runs at a time,
    preventing race conditions under pytest-xdist or multithreaded tests.
    """
    _LOG_CLEANUP_LOCK = threading.Lock()

    with _LOG_CLEANUP_LOCK:
        for logger in _iter_all_loggers():
            for h in list(logger.handlers):
                with suppress(Exception):
                    h.flush()
                with suppress(Exception):
                    h.close()
                with suppress(Exception):
                    logger.removeHandler(h)


def read_tail_complete_lines(
    path: Path, *, chunk_bytes: int, encoding: str = "utf-8"
) -> list[str]:
    """
    Read the tail of a JSONL file, preserving only complete lines.

    Robust to rotations/permissions/encoding:
    - Seeks near the end of file (chunk_bytes)
    - Drops a potentially truncated first/last line
    - Normalizes newlines
    """
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            buf = buf.split("\n", 1)[-1]  # drop possibly truncated first line

        buf = buf.replace("\r\n", "\n")
        raw_lines = buf.split("\n")

        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]  # drop last incomplete line

        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        return []
