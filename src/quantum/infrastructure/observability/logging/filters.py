import json
import logging
import os
import re
import threading
import time

from quantum.infrastructure.observability.logging.constants import get_audit_allowlist
from quantum.infrastructure.observability.metrics.health import logging_redactions_total

NOISY_LOGGERS = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk._shared_internal",
}
_SUFFIX_V1 = re.compile(r"_v1$")


class IgnoreLibrariesFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return all(not record.name.startswith(n) for n in NOISY_LOGGERS)


class LoggingContextFilter(logging.Filter):
    def __init__(self, env: str) -> None:
        super().__init__()
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:
        record.env = self.env
        return True


class MonotonicTimestampFilter(logging.Filter):
    """Injects a monotonic timestamp (ms) at the earliest in the logging cycle."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "ts_monotonic_ms"):
            record.ts_monotonic_ms = time.monotonic_ns() // 1_000_000
        return True


class AuditEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self._version = os.getenv("QUANTUM_AUDIT_EVENTS_VERSION", "v1").lower()
        self._allow = get_audit_allowlist(self._version)

    def filter(self, record: logging.LogRecord) -> bool:
        ev = getattr(record, "event", None)
        if not isinstance(ev, dict):
            return False
        name = ev.get("event_name")
        if not isinstance(name, str) or not name:
            return False
        n = name.strip().lower()
        if n.endswith("_v1"):
            n = _SUFFIX_V1.sub("", n)
        return n in self._allow


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


class RateLimitFilter(logging.Filter):
    def __init__(self, max_per_sec: float = 100.0):
        super().__init__()
        self._tokens = max_per_sec
        self._rate = max_per_sec
        self._t = time.monotonic()
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        with self._lock:
            now = time.monotonic()
            self._tokens += (now - self._t) * self._rate
            self._t = now
            if self._tokens > self._rate:
                self._tokens = self._rate
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False


class InfoSamplerFilter(logging.Filter):
    def __init__(self, sample_every: int = 10):
        super().__init__()
        self._n = max(1, int(sample_every))  # <=1 → no sampling
        self._i = 0
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno != logging.INFO or self._n <= 1:
            return True
        with self._lock:
            self._i = (self._i + 1) % self._n
            return self._i == 0


class StaticFieldsFilter(logging.Filter):
    """
    Injects stable fields (service_name / namespace / version) into each LogRecord,
    so that the formatter doesn't have to read environment variables.
    """

    def __init__(
        self, *, service_name: str, service_namespace: str, service_version: str
    ) -> None:
        super().__init__()
        self._service_name = service_name
        self._service_namespace = service_namespace
        self._service_version = service_version

    def filter(self, record: logging.LogRecord) -> bool:
        # Do not overwrite if already explicitly provided in the record
        if not hasattr(record, "service_name"):
            record.service_name = self._service_name
        if not hasattr(record, "service_namespace"):
            record.service_namespace = self._service_namespace
        if not hasattr(record, "service_version"):
            record.service_version = self._service_version
        return True
