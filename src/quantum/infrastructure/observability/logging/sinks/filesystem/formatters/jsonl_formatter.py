from __future__ import annotations

import json
import logging

from typing import Protocol


class RecordFormatter(Protocol):
    """Strict typing for safety-critical formatters."""

    def format(self, record: logging.LogRecord) -> str: ...


class JSONLRecordFormatter:
    """
    Converts LogRecord into a compact JSONL line.
    Safety-grade:
    - deterministic key ordering
    - no allow_nan
    - no schema logic here
    """

    __slots__ = ("_instance_id",)

    def __init__(self, instance_id: str) -> None:
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": record.created,
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "instance_id": self._instance_id,
        }

        if hasattr(record, "event"):
            data["event"] = record.event

        return json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
