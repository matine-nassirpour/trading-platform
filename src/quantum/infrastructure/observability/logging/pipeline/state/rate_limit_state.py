import threading
import time

from dataclasses import dataclass, field


@dataclass(slots=True)
class RateLimitState:
    """
    Thread-safe token bucket state for RateLimitStep.
    Clean separation of control logic vs. mutable state.
    """

    max_per_sec: float
    available_tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: threading.Lock = threading.Lock()

    def __post_init__(self) -> None:
        self.available_tokens = self.max_per_sec
        self.last_refill = time.monotonic()

    def consume_token(self) -> bool:
        """
        Returns True if the step is allowed to emit the record.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            # refill tokens
            self.available_tokens = min(
                self.max_per_sec,
                self.available_tokens + elapsed * self.max_per_sec,
            )

            # consume 1 token if available
            if self.available_tokens >= 1.0:
                self.available_tokens -= 1.0
                return True

            return False
