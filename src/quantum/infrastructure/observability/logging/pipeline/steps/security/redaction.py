from __future__ import annotations

import json
import logging
import re

from typing import Any, Final

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_redactions_total,
)

LOGGER: Final = logging.getLogger(__name__)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
SECRET_KEYS: Final[set[str]] = {
    "password",
    "secret",
    "token",
    "api_key",
    "access_key",
    "auth",
    "authorization",
    "bearer",
    "client_secret",
    "refresh_token",
    "session_id",
}

_JWT_RE: Final[re.Pattern[str]] = re.compile(
    r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
)

_HEX32_RE: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-fA-F]{32,}\b")

_MAX_VALUE_LEN: Final[int] = 5_000


class RedactionStep(PipelineStep):
    """
    Recursively sanitizes log record payloads:
        - redacts secrets based on key names
        - redacts JWT-like or high-entropy values
        - truncates excessively long strings
    """

    def _redact_value(self, value: Any) -> Any:
        """Redact a single value or recursively process containers."""
        # ─── dict
        if isinstance(value, dict):
            return {
                k: "[REDACTED]" if k.lower() in SECRET_KEYS else self._redact_value(v)
                for k, v in value.items()
            }

        # ─── list
        if isinstance(value, list):
            return [self._redact_value(v) for v in value]

        # ─── string
        if isinstance(value, str):
            s = value

            # truncate oversized string
            if len(s) > _MAX_VALUE_LEN:
                s = s[:_MAX_VALUE_LEN] + "…"

            # redact token-like patterns
            if _JWT_RE.search(s) or _HEX32_RE.search(s):
                return "[REDACTED]"

            return s

        # ─── primitive / any other
        return value

    def process(self, record: logging.LogRecord) -> object | None:
        """
        Applies redaction to:
            - record.attrs (structured attributes)
            - record.msg   (event/message text)
        Always returns the record (never drops).
        """
        modified = False

        # ─── Redact structured attrs
        attrs = getattr(record, "attrs", None)
        if isinstance(attrs, dict):
            before = json.dumps(attrs, ensure_ascii=False)
            record.attrs = self._redact_value(attrs)
            after = json.dumps(record.attrs, ensure_ascii=False)
            if after != before:
                modified = True

        # ─── Redact message string
        msg = getattr(record, "msg", None)
        if isinstance(msg, str):
            redacted = msg
            redacted = _JWT_RE.sub("[REDACTED]", redacted)
            redacted = _HEX32_RE.sub("[REDACTED]", redacted)

            if len(redacted) > _MAX_VALUE_LEN:
                redacted = redacted[:_MAX_VALUE_LEN] + "…"

            if redacted != msg:
                modified = True
                record.msg = redacted

        # ─── 3. Metrics
        if modified:
            try:
                logging_redactions_total.inc()
            except Exception as exc:
                LOGGER.debug(
                    "RedactionStep: failed to increment logging_redactions_total",
                    exc_info=exc,
                )

        return record
