"""
Event Retry Policy
──────────────────
Reusable retry strategy for event publication.

This ensures that event emission shares the same
semantic consistency as other resilience policies.
"""

from __future__ import annotations

import asyncio
import logging
import random

from dataclasses import dataclass
from typing import Final

LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EventRetryConfig:
    max_retries: int = 3
    base_backoff_s: float = 0.2
    backoff_cap_s: float = 2.0
    enable_jitter: bool = True


class EventRetryPolicy:
    """Resilient retry strategy for event publishing."""

    def __init__(self, cfg: EventRetryConfig | None = None) -> None:
        self._cfg = cfg or EventRetryConfig()
        self._rand = random.SystemRandom()

    def _compute_delay(self, attempt: int) -> float:
        delay = self._cfg.base_backoff_s * (2 ** (attempt - 1))
        if self._cfg.enable_jitter:
            delay *= self._rand.uniform(0.8, 1.3)
        return min(delay, self._cfg.backoff_cap_s)

    async def execute_with_retry(self, operation_name: str, coro) -> None:
        """Execute a coroutine with bounded retry and exponential backoff."""
        for attempt in range(1, self._cfg.max_retries + 1):
            try:
                await coro()
                if attempt > 1:
                    LOGGER.debug(
                        "[EventRetry] %s succeeded on attempt=%d",
                        operation_name,
                        attempt,
                    )
                return
            except Exception as exc:
                if attempt >= self._cfg.max_retries:
                    LOGGER.error(
                        "[EventRetry] %s aborted after %d attempts (exc=%s)",
                        operation_name,
                        attempt,
                        type(exc).__name__,
                    )
                    raise
                delay = self._compute_delay(attempt)
                LOGGER.warning(
                    "[EventRetry] %s failed (attempt=%d) — retrying in %.2fs",
                    operation_name,
                    attempt,
                    delay,
                )
                await asyncio.sleep(delay)
