import json
import logging
import re

from typing import Any, Final

from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_redactions_total,
)

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
# JWT-like or high-entropy patterns
_JWT_RE: Final[re.Pattern[str]] = re.compile(
    r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
)
_HEX32_RE: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-fA-F]{32,}\b")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Filter                                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
class RedactFilter(logging.Filter):
    """
    Recursively scans and redacts sensitive data from log records.
    """

    # Maximum allowed string value length (beyond this → truncated)
    MAX_VALUE_LEN: Final[int] = 5_000

    def _redact_recursive(self, obj: Any) -> Any:
        """
        Recursively redacts secrets from nested dicts, lists, or strings.
        """
        if isinstance(obj, dict):
            return {
                k: (
                    "[REDACTED]"
                    if k.lower() in SECRET_KEYS
                    else self._redact_recursive(v)
                )
                for k, v in obj.items()
            }

        if isinstance(obj, list):
            return [self._redact_recursive(v) for v in obj]

        if isinstance(obj, str):
            s = obj
            if len(s) > self.MAX_VALUE_LEN:
                s = s[: self.MAX_VALUE_LEN] + "…"
            if _JWT_RE.search(s) or _HEX32_RE.search(s):
                return "[REDACTED]"
            return s

        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Applies redaction logic to the LogRecord in-place.
        Increments the redaction counter when a payload is modified.
        """
        attrs = getattr(record, "attrs", None)
        if isinstance(attrs, dict):
            before_len = len(json.dumps(attrs, ensure_ascii=False))
            record.attrs = self._redact_recursive(attrs)
            after_len = len(json.dumps(record.attrs, ensure_ascii=False))  # type: ignore[attr-defined]
            if after_len < before_len:
                logging_redactions_total.inc()

        msg = getattr(record, "msg", None)
        if isinstance(msg, str):
            redacted = _JWT_RE.sub("[REDACTED]", msg)
            redacted = _HEX32_RE.sub("[REDACTED]", redacted)
            if len(redacted) > self.MAX_VALUE_LEN:
                redacted = redacted[: self.MAX_VALUE_LEN] + "…"
            record.msg = redacted

        return True
