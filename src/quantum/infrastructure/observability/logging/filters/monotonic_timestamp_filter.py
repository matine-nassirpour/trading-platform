import logging
import time


class MonotonicTimestampFilter(logging.Filter):
    """
    Adds a 'ts_monotonic_ms' attribute to each LogRecord if absent.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Ensures every record has a monotonic timestamp field (ts_monotonic_ms).
        """
        if not hasattr(record, "ts_monotonic_ms"):
            record.ts_monotonic_ms = time.monotonic_ns() // 1_000_000
        return True
