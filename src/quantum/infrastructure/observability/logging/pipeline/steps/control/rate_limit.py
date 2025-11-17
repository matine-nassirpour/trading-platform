from __future__ import annotations

import logging
import threading
import time

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)


class RateLimitStep(PipelineStep):
    """
    Controls the rate of emitted log records using a token bucket algorithm.
    """

    __slots__ = ("_max_per_sec", "_available_tokens", "_last_refill", "_lock")

    def __init__(self, max_per_sec: float = 100.0) -> None:
        self._max_per_sec = max(0.1, float(max_per_sec))
        self._available_tokens = self._max_per_sec
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def process(self, record: logging.LogRecord) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._last_refill = now

            self._available_tokens = min(
                self._max_per_sec, self._available_tokens + elapsed * self._max_per_sec
            )

            if self._available_tokens >= 1.0:
                self._available_tokens -= 1.0
                return True

            return False
