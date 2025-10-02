import logging
import time

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
    AUDIT_EVENTS = {
        "order_submit_v1",
        "order_ack_v1",
        "order_fill_v1",
        "order_reject_v1",
        "killswitch_trigger_v1",
        "reconciliation_v1",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        ev = getattr(record, "event", None)
        return isinstance(ev, dict) and ev.get("event_name") in self.AUDIT_EVENTS


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
