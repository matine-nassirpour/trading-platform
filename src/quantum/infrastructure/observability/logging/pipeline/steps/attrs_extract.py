from __future__ import annotations

import logging

from contextlib import suppress
from typing import Any

from quantum.infrastructure.observability.logging.constants import EXCLUDED_STD_FIELDS
from quantum.infrastructure.observability.logging.utils.json_sanitize import (
    json_sanitize,
)


class AttrsExtractStep:
    """Extract sanitized attributes from a LogRecord."""

    def apply(self, record: logging.LogRecord) -> None:
        """Extract and sanitize attributes into `record.attrs`."""

        raw: dict[str, Any] = {
            k: v for k, v in record.__dict__.items() if k not in EXCLUDED_STD_FIELDS
        }

        attrs: dict[str, Any] = {}

        for key, value in raw.items():
            self._normalize_field(key, value, attrs)

        # Sanitize entire structure once it's assembled
        record.attrs = json_sanitize(attrs)

    @staticmethod
    def _normalize_field(key: str, value: Any, attrs: dict[str, Any]) -> None:
        """
        Handle special-case fields:
        - exception blocks
        - embedded attrs
        - default key/value assignment
        """
        if key == "exception":
            with suppress(Exception):
                if isinstance(value, dict):
                    attrs["exception_obj"] = value
                elif value is not None:
                    attrs["exception_text"] = str(value)
            return

        if key == "attrs" and isinstance(value, dict):
            # Merge pre-existing attrs fields (handlers/emitters)
            attrs.update(value)
            return

        attrs[key] = value
