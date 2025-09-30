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
