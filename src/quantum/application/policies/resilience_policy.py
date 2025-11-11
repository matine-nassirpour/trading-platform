from __future__ import annotations

import asyncio
import logging
import random
import time

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Generic, ParamSpec, TypeVar, cast

from quantum.application.policies.retry_policy import DefaultRetryPolicy, RetryPolicy
from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort

P = ParamSpec("P")
R = TypeVar("R")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration Model                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class ResilienceConfig:
    """Immutable resilience configuration parameters."""

    max_retries: int = 3
    timeout_sec: float = 5.0
    base_backoff: float = 0.5
    backoff_cap: float = 5.0
    enable_jitter: bool = True
    max_total_time: float | None = None  # Optional global deadline (seconds)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Logging Adapter                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ResilienceLogger:
    """Adapter for consistent structured logging across sync/async flows."""

    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger(__name__)

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
                    "event": "success",
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
                    "event": "failure",
                }
            },
        )

    def log_retry(self, operation: str, attempt: int, delay: float) -> None:
        self._logger.debug(
            "[Resilience] Retrying %s in %.2fs (attempt=%d)",
            operation,
            delay,
            attempt,
            extra={
                "attrs": {
                    "operation": operation,
                    "attempt": attempt,
                    "delay": delay,
                    "event": "retry",
                }
            },
        )

    def log_abort(
        self, operation: str, attempt: int, total_time: float, exc: Exception | None
    ) -> None:
        level = logging.ERROR if exc else logging.WARNING
        self._logger.log(
            level,
            "[Resilience] %s aborted after %d attempts (%.2fs total) — %s",
            operation,
            attempt,
            total_time,
            type(exc).__name__ if exc else "max_time_exceeded",
            extra={
                "attrs": {
                    "operation": operation,
                    "attempt": attempt,
                    "error": str(exc) if exc else None,
                    "total_time_s": total_time,
                    "event": "abort",
                }
            },
        )


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Backoff Strategy                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
        delay = self._base * (2 ** (attempt - 1))
        if self._jitter:
            delay *= self._rand(0.8, 1.3)
        return float(min(delay, self._cap))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Domain Exception for Aborts                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ResilienceAbortError(RuntimeError):
    """Raised when retries are exhausted or deadline exceeded."""

    def __init__(self, operation: str, attempts: int, cause: Exception | None = None):
        msg = f"[{operation}] aborted after {attempts} attempts"
        if cause:
            msg += f" — cause: {type(cause).__name__}: {cause}"
        super().__init__(msg)
        self.operation = operation
        self.attempts = attempts
        self.__cause__ = cause  # keep original cause for traceback chain


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Core Executor                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ResilienceExecutor(Generic[P, R]):
    """Unified executor for resilient sync/async calls."""

    def __init__(
        self,
        *,
        operation: str,
        timeout_runner: TimeoutRunnerPort,
        policy: RetryPolicy | None = None,
        cfg: ResilienceConfig | None = None,
        logger: ResilienceLogger | None = None,
    ) -> None:
        self.operation = operation
        self.timeout_runner = timeout_runner
        self.policy = policy or DefaultRetryPolicy()
        self.cfg = cfg or ResilienceConfig()
        self.logger = logger or ResilienceLogger()
        self.backoff = BackoffStrategy(
            base=self.cfg.base_backoff,
            cap=self.cfg.backoff_cap,
            jitter=self.cfg.enable_jitter,
        )

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _compute_delay(self, attempt: int, elapsed_total: float) -> float:
        """Compute backoff delay while respecting max_total_time if set."""
        delay = self.backoff.compute_delay(attempt)
        if (
            self.cfg.max_total_time is not None
            and elapsed_total + delay > self.cfg.max_total_time
        ):
            remaining = self.cfg.max_total_time - elapsed_total
            return max(0.0, remaining)
        return delay

    def _should_abort(
        self, attempt: int, elapsed_total: float, result: Any, exc: Exception | None
    ) -> bool:
        """Determine if retries should stop based on policy or limits."""
        timeout_reached = (
            self.cfg.max_total_time is not None
            and elapsed_total >= self.cfg.max_total_time
        )
        return (
            attempt >= self.cfg.max_retries
            or not self.policy.should_retry(result, exc)
            or timeout_reached
        )

    def _handle_post_attempt(
        self,
        attempt: int,
        start_global: float,
        result: object,
        last_exc: Exception | None,
    ) -> float:
        """
        Common post-attempt handler (sync + async).
        Handles abort decision, logging, and backoff computation.
        Returns the next delay (seconds) or raises ResilienceAbortError.
        """
        elapsed = time.time() - start_global
        if self._should_abort(attempt, elapsed, result, last_exc):
            self.logger.log_abort(self.operation, attempt, elapsed, last_exc)
            raise ResilienceAbortError(self.operation, attempt, last_exc) from last_exc

        delay = self._compute_delay(attempt, elapsed)
        self.logger.log_retry(self.operation, attempt, delay)
        return delay

    # --------------------------------------------------------------------------
    # Synchronous Execution
    # --------------------------------------------------------------------------
    def execute_sync(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        attempt = 0
        start_global = time.time()
        result: Any | None = None

        while True:
            attempt += 1
            start = time.time()
            try:
                result = self.timeout_runner.run_with_timeout_sync(
                    func,
                    *args,
                    timeout_sec=self.cfg.timeout_sec,
                    call_name=self.operation,
                    **kwargs,
                )
                latency_ms = int((time.time() - start) * 1000)
                self.logger.log_success(self.operation, attempt, latency_ms)
                return result

            except Exception as e:
                last_exc = e
                latency_ms = int((time.time() - start) * 1000)
                self.logger.log_failure(self.operation, attempt, e, latency_ms)

            delay = self._handle_post_attempt(attempt, start_global, result, last_exc)
            time.sleep(delay)

    # --------------------------------------------------------------------------
    # Asynchronous Execution
    # --------------------------------------------------------------------------
    async def execute_async(
        self, func: Callable[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        attempt = 0
        start_global = time.time()

        while True:
            attempt += 1
            start = time.time()
            try:
                result: R = await self.timeout_runner.run_with_timeout_async(
                    func,
                    *args,
                    timeout_sec=self.cfg.timeout_sec,
                    call_name=self.operation,
                    **kwargs,
                )
                latency_ms = int((time.time() - start) * 1000)
                self.logger.log_success(self.operation, attempt, latency_ms)
                return result

            except asyncio.CancelledError:
                self.logger.log_abort(
                    self.operation, attempt, time.time() - start_global, None
                )
                raise

            except Exception as e:
                last_exc = e
                latency_ms = int((time.time() - start) * 1000)
                self.logger.log_failure(self.operation, attempt, e, latency_ms)

            delay = self._handle_post_attempt(attempt, start_global, result, last_exc)
            await asyncio.sleep(delay)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public decorators                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
def resilient_call(
    func: Callable[P, R] | None = None,
    *,
    timeout_runner: TimeoutRunnerPort | None = None,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    """Decorator for resilient synchronous operations."""

    def decorator(inner_func: Callable[P, R]) -> Callable[P, R]:
        op_name = inner_func.__qualname__

        @wraps(inner_func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if timeout_runner is None:
                raise RuntimeError(
                    f"[{op_name}] resilient_call used without timeout_runner injection"
                )
            executor: ResilienceExecutor[P, R] = ResilienceExecutor(
                operation=op_name, timeout_runner=timeout_runner, policy=policy, cfg=cfg
            )
            return executor.execute_sync(inner_func, *args, **kwargs)

        wrapped = cast(Callable[P, R], wrapper)
        wrapped._resilience_call_name = op_name  # type: ignore[attr-defined]
        return wrapped

    return decorator if func is None else decorator(func)


def resilient_async_call(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    timeout_runner: TimeoutRunnerPort | None,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> (
    Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]
    | Callable[P, Awaitable[R]]
):
    """Decorator for resilient asynchronous operations."""

    def decorator(inner_func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        op_name = inner_func.__qualname__

        @wraps(inner_func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if timeout_runner is None:
                raise RuntimeError(
                    f"[{op_name}] resilient_async_call used without timeout_runner injection"
                )
            executor: ResilienceExecutor[P, R] = ResilienceExecutor(
                operation=op_name, timeout_runner=timeout_runner, policy=policy, cfg=cfg
            )
            return await executor.execute_async(inner_func, *args, **kwargs)

        wrapped = cast(Callable[P, Awaitable[R]], wrapper)
        wrapped._resilience_call_name = op_name  # type: ignore[attr-defined]
        return wrapped

    return decorator if func is None else decorator(func)
