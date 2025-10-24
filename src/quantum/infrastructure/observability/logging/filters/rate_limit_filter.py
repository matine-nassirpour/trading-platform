import logging
import threading
import time


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
