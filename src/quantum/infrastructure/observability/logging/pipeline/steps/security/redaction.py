import json
import logging
import re

from collections.abc import Mapping
from contextlib import suppress
from typing import Any, Final, Protocol, cast

from quantum.infrastructure.observability.foundation.metrics.c0_metric_registry import (
    define_counter,
)
from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)

LOGGER: Final = logging.getLogger(__name__)

_LOGGING_REDACTIONS_TOTAL: Final = define_counter("logging_redactions_total")

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
    r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"
)

_HEX_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-fA-F]{40,}\b")

_MAX_VALUE_LEN: Final[int] = 5_000


class _RecordWithAttrs(Protocol):
    attrs: Mapping[str, Any]


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
        if _JWT_RE.search(s) or _HEX_TOKEN_RE.search(s):
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

    __slots__ = ()

    def process(self, record: logging.LogRecord) -> bool:
        modified = False

        try:
            # Structured attributes
            attrs = getattr(record, "attrs", None)
            if isinstance(attrs, dict):
                before = json.dumps(attrs, ensure_ascii=False)

                redacted = _redact_value(attrs)
                record.attrs = redacted if isinstance(redacted, dict) else {}

                rec = cast(_RecordWithAttrs, cast(object, record))
                after = json.dumps(rec.attrs, ensure_ascii=False)

                if before is not None and after is not None and before != after:
                    modified = True

            # Message redaction
            msg = getattr(record, "msg", None)
            if isinstance(msg, str):
                redacted_msg = msg

                redacted_msg = _JWT_RE.sub("[REDACTED]", redacted_msg)
                redacted_msg = _HEX_TOKEN_RE.sub("[REDACTED]", redacted_msg)

                if len(redacted_msg) > _MAX_VALUE_LEN:
                    redacted_msg = redacted_msg[:_MAX_VALUE_LEN] + "…"

                if redacted_msg != msg:
                    record.msg = redacted_msg
                    modified = True

            # Metrics
            if modified:
                with suppress(Exception):
                    _LOGGING_REDACTIONS_TOTAL.inc()

            return True

        except Exception as exc:
            # Absolute fail-safe
            LOGGER.debug("RedactionStep failed but recovered", exc_info=exc)
            return True
