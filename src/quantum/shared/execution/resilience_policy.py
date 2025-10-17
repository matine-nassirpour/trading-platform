"""
Resilience Policy — Dynamic, Observable, and Industry-Grade
──────────────────────────────────────────────────────────────
Provides fully configurable, testable, and composable resilience mechanisms
for synchronous and asynchronous operations.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Generic, ParamSpec, TypeVar

from quantum.shared.execution.retry_policy import DefaultRetryPolicy, RetryPolicy
from quantum.shared.execution.timeout_utils import (
    run_with_timeout_async,
    run_with_timeout_sync,
)

# Generic typing
P = ParamSpec("P")
R = TypeVar("R")


# ──────────────────────────────────────────────────────────────────────────────
# Configuration Model
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResilienceConfig:
    """Immutable resilience configuration parameters."""

    max_retries: int = 3
    timeout_sec: float = 5.0
    base_backoff: float = 0.5
    backoff_cap: float = 5.0
    enable_jitter: bool = True
    max_total_time: float | None = None  # Optional global deadline


# ──────────────────────────────────────────────────────────────────────────────
# Logging Adapter
# ──────────────────────────────────────────────────────────────────────────────


class ResilienceLogger:
    """Adapter for consistent structured logging across sync/async flows."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def log_success(self, operation: str, attempt: int, latency_ms: int) -> None:
        self._logger.debug(
            "[Resilience] %s attempt %d succeeded in %dms",
            operation,
            attempt,
            latency_ms,
            extra={
                "attrs": {
                    "operation": operation,
                    "attempt": attempt,
                    "latency_ms": latency_ms,
                }
            },
        )

    def log_failure(
        self, operation: str, attempt: int, exc: Exception, latency_ms: int
    ) -> None:
        self._logger.warning(
            "[Resilience] %s attempt %d failed: %s",
            operation,
            attempt,
            exc,
            extra={
                "attrs": {
                    "operation": operation,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "latency_ms": latency_ms,
                }
            },
        )

    def log_retry(self, operation: str, attempt: int, delay: float) -> None:
        self._logger.debug(
            "[Resilience] Retrying %s in %.2fs",
            operation,
            delay,
            extra={"attrs": {"operation": operation, "attempt": attempt}},
        )

    def log_abort(
        self, operation: str, attempt: int, total_time: float, exc: Exception | None
    ) -> None:
        level = logging.ERROR if exc else logging.WARNING
        self._logger.log(
            level,
            "[Resilience] %s aborted after %d attempts (%.2fs total)",
            operation,
            attempt,
            total_time,
            extra={
                "attrs": {
                    "operation": operation,
                    "attempt": attempt,
                    "error": str(exc) if exc else None,
                    "total_time_s": total_time,
                }
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Backoff Strategy
# ──────────────────────────────────────────────────────────────────────────────


class BackoffStrategy:
    """Computes exponential backoff delays with optional jitter."""

    def __init__(
        self,
        base: float,
        cap: float,
        jitter: bool = True,
        randomizer: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self._base = base
        self._cap = cap
        self._jitter = jitter
        self._rand = randomizer

    def compute_delay(self, attempt: int) -> float:
        """Compute the next backoff delay (seconds)."""
        delay = self._base * (2 ** (attempt - 1))
        if self._jitter:
            delay *= self._rand(0.8, 1.3)
        return min(delay, self._cap)


# ──────────────────────────────────────────────────────────────────────────────
# Core Executor
# ──────────────────────────────────────────────────────────────────────────────


class ResilienceExecutor(Generic[P, R]):
    """Unified executor for resilient sync/async calls."""

    def __init__(
        self,
        *,
        operation: str,
        policy: RetryPolicy | None = None,
        cfg: ResilienceConfig | None = None,
        backoff: BackoffStrategy | None = None,
        logger: ResilienceLogger | None = None,
        time_provider: Callable[[], float] = time.time,
        sleep_fn: Callable[[float], None] = time.sleep,
        async_sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.operation = operation
        self.policy = policy or DefaultRetryPolicy()
        self.cfg = cfg or ResilienceConfig()
        self.backoff = backoff or BackoffStrategy(
            base=self.cfg.base_backoff,
            cap=self.cfg.backoff_cap,
            jitter=self.cfg.enable_jitter,
        )
        self.logger = logger or ResilienceLogger(logging.getLogger(__name__))
        self.now = time_provider
        self.sleep_fn = sleep_fn
        self.async_sleep_fn = async_sleep_fn

    # ─── Shared Retry Logic
    def _should_abort(
        self, attempt: int, elapsed_total: float, result: Any, exc: Exception | None
    ) -> bool:
        """Determine if retries should stop based on policy or limits."""
        return (
            attempt >= self.cfg.max_retries
            or not self.policy.should_retry(result, exc)
            or (self.cfg.max_total_time and elapsed_total > self.cfg.max_total_time)
        )

    def _handle_post_attempt(
        self, attempt: int, start_global: float, result: Any, exc: Exception | None
    ) -> float | None:
        """Return the next delay or None if aborted."""
        elapsed_total = self.now() - start_global
        if self._should_abort(attempt, elapsed_total, result, exc):
            self.logger.log_abort(self.operation, attempt, elapsed_total, exc)
            if exc:
                raise exc
            return None
        delay = self.backoff.compute_delay(attempt)
        self.logger.log_retry(self.operation, attempt, delay)
        return delay

    # ─── Synchronous Execution
    def execute_sync(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        attempt = 0
        start_global = self.now()
        result: Any | None = None

        while True:
            attempt += 1
            start = self.now()
            try:
                result = run_with_timeout_sync(
                    func,
                    *args,
                    seconds=self.cfg.timeout_sec,
                    call_name=self.operation,
                    **kwargs,
                )
                latency = int((self.now() - start) * 1000)
                self.logger.log_success(self.operation, attempt, latency)
                return result
            except Exception as e:
                exc = e
                latency = int((self.now() - start) * 1000)
                self.logger.log_failure(self.operation, attempt, e, latency)

            delay = self._handle_post_attempt(attempt, start_global, result, exc)
            if delay is None:
                return result
            self.sleep_fn(delay)

    # ─── Asynchronous Execution
    async def execute_async(
        self, func: Callable[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        attempt = 0
        start_global = self.now()
        result: Any | None = None

        while True:
            attempt += 1
            start = self.now()
            try:
                result = await run_with_timeout_async(
                    func,
                    *args,
                    timeout_sec=self.cfg.timeout_sec,
                    call_name=self.operation,
                    **kwargs,
                )
                latency = int((self.now() - start) * 1000)
                self.logger.log_success(self.operation, attempt, latency)
                return result
            except asyncio.CancelledError:
                self.logger.log_abort(
                    self.operation, attempt, self.now() - start_global, exc=None
                )
                raise
            except Exception as e:
                exc = e
                latency = int((self.now() - start) * 1000)
                self.logger.log_failure(self.operation, attempt, e, latency)

            delay = self._handle_post_attempt(attempt, start_global, result, exc)
            if delay is None:
                return result
            await self.async_sleep_fn(delay)


# ──────────────────────────────────────────────────────────────────────────────
# Public Decorators
# ──────────────────────────────────────────────────────────────────────────────


def resilient_call(
    operation: str,
    *,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for resilient synchronous operations."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            executor = ResilienceExecutor(operation=operation, policy=policy, cfg=cfg)
            return executor.execute_sync(func, *args, **kwargs)

        return wrapper

    return decorator


def resilient_async_call(
    operation: str,
    *,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator for resilient asynchronous operations."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            executor = ResilienceExecutor(operation=operation, policy=policy, cfg=cfg)
            return await executor.execute_async(func, *args, **kwargs)

        return wrapper

    return decorator
