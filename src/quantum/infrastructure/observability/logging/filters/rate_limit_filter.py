import logging
import threading
import time


class RateLimitFilter(logging.Filter):
    """
    Controls the rate of emitted log records using a token bucket algorithm.
    """

    def __init__(self, max_per_sec: float = 100.0):
        super().__init__()
        self._max_per_sec = max(0.1, float(max_per_sec))
        self._available_tokens = max_per_sec
        self._last_refill_time = time.monotonic()
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Allows or suppresses a log record based on the token bucket fill rate.
        Thread-safe.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill_time
            self._last_refill_time = now

            self._available_tokens = min(
                self._max_per_sec, self._available_tokens + elapsed * self._max_per_sec
            )

            if self._available_tokens >= 1.0:
                self._available_tokens -= 1.0
                return True

            return False
