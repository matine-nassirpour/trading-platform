from __future__ import annotations

import json
import logging

from typing import Any

from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)


class JSONLRecordFormatter:
    """
    Safety-grade JSONL formatter.
    Guarantees:
    - NEVER raise
    - deterministic output
    - stable fallback behavior
    - no schema logic / no enrichment

    Responsibilities:
    - Convert LogRecord into compact JSONL dict
    - Reject or neutralize unserializable values
    - Fallback minimal JSON on error
    """

    __slots__ = ("_instance_id",)

    def __init__(self, instance_id: str) -> None:
        self._instance_id = instance_id

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _safe_json_dumps(obj: Any) -> str:
        """
        json.dumps wrapper that NEVER raises.
        Any failure returns a compact fallback string.
        """
        try:
            return json.dumps(
                obj,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
        except Exception:
            # Fallback JSON: minimal and always valid
            return '{"error":"jsonl_format_failed"}'

    @staticmethod
    def _safe_message(record: logging.LogRecord) -> str:
        try:
            msg = record.getMessage()
            return msg if isinstance(msg, str) else str(msg)
        except Exception:
            return "<message_unavailable>"

    # --------------------------------------------------------------------------
    # Core logic
    # --------------------------------------------------------------------------
    def format(self, record: logging.LogRecord) -> str:
        try:
            data = {
                "ts": record.created,
                "logger": record.name,
                "level": record.levelname,
                "message": self._safe_message(record),
                "instance_id": self._instance_id,
            }

            event = getattr(record, "event", None)
            if isinstance(event, dict):
                data["event"] = json_sanitize(event)

            return self._safe_json_dumps(json_sanitize(data))

        except Exception:
            fallback = {
                "ts": getattr(record, "created", 0.0),
                "logger": getattr(record, "name", "<unknown>"),
                "level": getattr(record, "levelname", "ERROR"),
                "message": "jsonl_fatal_formatter_error",
                "instance_id": self._instance_id,
            }
            return self._safe_json_dumps(json_sanitize(fallback))
