import json
import logging
import re

from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_redactions_total,
)


class RedactFilter(logging.Filter):
    SECRETS_KEYS = {
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
    MAX_VALUE_LEN = 5_000
    # JWT-like or long high-entropy tokens (very heuristic)
    _JWT_RE = re.compile(
        r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
    )
    _HEX32_RE = re.compile(r"\b[0-9a-fA-F]{32,}\b")

    def _redact_recursive(self, obj):
        if isinstance(obj, dict):
            return {
                k: (
                    "[REDACTED]"
                    if k.lower() in self.SECRETS_KEYS
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
            if self._JWT_RE.search(s) or self._HEX32_RE.search(s):
                return "[REDACTED]"
            return s
        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        attrs = getattr(record, "attrs", None)
        if isinstance(attrs, dict):
            before_len = len(json.dumps(attrs, ensure_ascii=False))
            record.attrs = self._redact_recursive(attrs)
            after_len = len(json.dumps(record.attrs, ensure_ascii=False))
            if after_len < before_len:
                logging_redactions_total.inc()
        msg = getattr(record, "msg", None)
        if isinstance(msg, str):
            # Redaction by regex (JWT, long hexes)
            redacted = self._JWT_RE.sub("[REDACTED]", msg)
            redacted = self._HEX32_RE.sub("[REDACTED]", redacted)

            # Possible truncation
            if len(redacted) > self.MAX_VALUE_LEN:
                redacted = redacted[: self.MAX_VALUE_LEN] + "…"
            record.msg = redacted

        return True
