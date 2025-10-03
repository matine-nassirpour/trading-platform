import logging
import os
import threading
import time

from quantum.infrastructure.observability.logging.constants import get_audit_whitelist

NOISY_LOGGERS = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
}


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
        self._version = os.getenv("QUANTUM_AUDIT_EVENTS_VERSION", "v1")
        self._whitelist = get_audit_whitelist(self._version)

    def filter(self, record: logging.LogRecord) -> bool:
        ev = getattr(record, "event", None)
        if not isinstance(ev, dict):
            return False
        name = ev.get("event_name")
        return isinstance(name, str) and name in self._whitelist


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
        if isinstance(obj, str) and len(obj) > self.MAX_VALUE_LEN:
            return obj[: self.MAX_VALUE_LEN] + "…"
        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        attrs = getattr(record, "attrs", None)
        if isinstance(attrs, dict):
            record.attrs = self._redact_recursive(attrs)
        msg = getattr(record, "msg", None)
        if isinstance(msg, str) and len(msg) > self.MAX_VALUE_LEN:
            record.msg = msg[: self.MAX_VALUE_LEN] + "…"
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
        self._i = 0
        self._n = sample_every
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno != logging.INFO:
            return True
        with self._lock:
            self._i = (self._i + 1) % self._n
            return self._i == 0
