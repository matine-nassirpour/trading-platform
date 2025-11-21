from __future__ import annotations

import json
import logging
import re

from contextlib import suppress
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
SECRET_KEYS: Final[frozenset[str]] = frozenset(
    {
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
)

_JWT_RE: Final[re.Pattern[str]] = re.compile(
    r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
)

_HEX32_RE: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-fA-F]{32,}\b")

_MAX_VALUE_LEN: Final[int] = 5_000


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helper                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _redact_value(value: Any) -> Any:
    """
    Pure redaction utility — fully deterministic and never raises.
    """
    # dict
    if isinstance(value, dict):
        redacted = {}
        for k, v in value.items():
            lk = k.lower()
            if lk in SECRET_KEYS:
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _redact_value(v)
        return redacted

    # list
    if isinstance(value, list):
        return [_redact_value(v) for v in value]

    # string
    if isinstance(value, str):
        s = value

        if len(s) > _MAX_VALUE_LEN:
            s = s[:_MAX_VALUE_LEN] + "…"

        # redact token-like values
        if _JWT_RE.search(s) or _HEX32_RE.search(s):
            return "[REDACTED]"

        return s

    # primitive or unknown types
    return value


class RedactionStep(PipelineStep):
    """
    Recursively sanitizes log record payloads:
        - redacts secrets based on key names
        - redacts JWT-like or high-entropy values
        - truncates excessively long strings
    """

    def process(self, record: logging.LogRecord) -> bool:
        modified = False

        try:
            # Structured attributes
            attrs = getattr(record, "attrs", None)
            if isinstance(attrs, dict):
                before = json.dumps(attrs, ensure_ascii=False)

                redacted = _redact_value(attrs)
                record.attrs = redacted if isinstance(redacted, dict) else {}

                after = json.dumps(redacted, ensure_ascii=False)

                if before is not None and after is not None and before != after:
                    modified = True

            # Message redaction
            msg = getattr(record, "msg", None)
            if isinstance(msg, str):
                redacted_msg = msg

                redacted_msg = _JWT_RE.sub("[REDACTED]", redacted_msg)
                redacted_msg = _HEX32_RE.sub("[REDACTED]", redacted_msg)

                if len(redacted_msg) > _MAX_VALUE_LEN:
                    redacted_msg = redacted_msg[:_MAX_VALUE_LEN] + "…"

                if redacted_msg != msg:
                    record.msg = redacted_msg
                    modified = True

            # Metrics
            if modified:
                with suppress(Exception):
                    logging_redactions_total.inc()

            return True

        except Exception as exc:
            # Absolute fail-safe
            LOGGER.debug("RedactionStep failed but recovered", exc_info=exc)
            return True
