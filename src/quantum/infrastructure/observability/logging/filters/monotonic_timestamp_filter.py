import logging
import time


class MonotonicTimestampFilter(logging.Filter):
    """Injects a monotonic timestamp (ms) at the earliest in the logging cycle."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "ts_monotonic_ms"):
            record.ts_monotonic_ms = time.monotonic_ns() // 1_000_000
        return True
