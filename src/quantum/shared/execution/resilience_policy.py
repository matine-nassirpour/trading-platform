from __future__ import annotations

import asyncio
import functools
import logging
import os
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from quantum.shared.execution.retry_policy import should_retry
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R", bound=ExecutionResult)

# Defaults configurable via environment (.env or runtime)
_DEFAULT_MAX_RETRIES = int(os.getenv("QUANTUM_EXEC_RETRIES", "3"))
_DEFAULT_TIMEOUT = float(os.getenv("QUANTUM_EXEC_TIMEOUT", "5.0"))
_DEFAULT_BACKOFF = float(os.getenv("QUANTUM_EXEC_BACKOFF", "0.5"))
_DEFAULT_BACKOFF_MAX = float(os.getenv("QUANTUM_EXEC_BACKOFF_MAX", "5.0"))


def _compute_backoff(attempt: int, base: float, max_backoff: float) -> float:
    """Exponential backoff with cap."""
    return min(base * (2 ** (attempt - 1)), max_backoff)


@overload
def resilient_call(
    op_name: str,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    timeout_sec: float = _DEFAULT_TIMEOUT,
    base_backoff: float = _DEFAULT_BACKOFF,
    max_backoff: float = _DEFAULT_BACKOFF_MAX,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
@overload
def resilient_call(
    op_name: str,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    timeout_sec: float = _DEFAULT_TIMEOUT,
    base_backoff: float = _DEFAULT_BACKOFF,
    max_backoff: float = _DEFAULT_BACKOFF_MAX,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...


def resilient_call(
    op_name: str,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    timeout_sec: float = _DEFAULT_TIMEOUT,
    base_backoff: float = _DEFAULT_BACKOFF,
    max_backoff: float = _DEFAULT_BACKOFF_MAX,
):
    """
    Decorator providing retry, timeout and exponential backoff around
    sync or async functions returning an ExecutionResult.

    Usage:
    ------
        @resilient_call("send_order")
        def send_order(...): ...

        @resilient_call("fetch_data")
        async def fetch_data(...): ...
    """

    def decorator(func: Callable[..., R | Awaitable[R]]):
        is_async = asyncio.iscoroutinefunction(func)

        if not is_async:
            # ─── SYNC WRAPPER
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                attempt = 0
                last_result: ExecutionResult | None = None

                while attempt < max_retries:
                    attempt += 1
                    start = time.time()

                    try:
                        result = func(*args, **kwargs)
                        last_result = result

                        if not should_retry(result.code):
                            return result

                        logger.warning(
                            f"[{op_name}] Retryable error ({result.code}), "
                            f"attempt {attempt}/{max_retries}",
                            extra={"attrs": {"message": result.message}},
                        )

                    except Exception as e:
                        msg = f"{type(e).__name__}: {e}"
                        logger.exception(
                            f"[{op_name}] Exception on attempt {attempt}: {msg}"
                        )
                        last_result = ExecutionResult(
                            code=ExecutionCode.INTERNAL_FAIL,
                            message=msg,
                        )

                    elapsed = time.time() - start
                    if elapsed > timeout_sec:
                        logger.error(
                            f"[{op_name}] Timeout exceeded ({elapsed:.2f}s > {timeout_sec}s)",
                            extra={"attrs": {"attempt": attempt}},
                        )
                        last_result = ExecutionResult.fatal("Operation timeout")

                    if attempt < max_retries:
                        time.sleep(_compute_backoff(attempt, base_backoff, max_backoff))

                return last_result or ExecutionResult.fatal(
                    "No response after all retry attempts"
                )

            return sync_wrapper

        else:
            # ─── ASYNC WRAPPER
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                attempt = 0
                last_result: ExecutionResult | None = None

                while attempt < max_retries:
                    attempt += 1

                    try:
                        # enforce timeout using asyncio.wait_for
                        result = await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout_sec,
                        )
                        last_result = result

                        if not should_retry(result.code):
                            return result

                        logger.warning(
                            f"[{op_name}] Retryable error ({result.code}), "
                            f"attempt {attempt}/{max_retries}",
                            extra={"attrs": {"message": result.message}},
                        )

                    except TimeoutError:
                        logger.error(
                            f"[{op_name}] Timeout exceeded after {timeout_sec}s",
                            extra={"attrs": {"attempt": attempt}},
                        )
                        last_result = ExecutionResult.fatal("Operation timeout")

                    except Exception as e:
                        msg = f"{type(e).__name__}: {e}"
                        logger.exception(
                            f"[{op_name}] Exception on attempt {attempt}: {msg}"
                        )
                        last_result = ExecutionResult(
                            code=ExecutionCode.INTERNAL_FAIL,
                            message=msg,
                        )

                    if attempt < max_retries:
                        await asyncio.sleep(
                            _compute_backoff(attempt, base_backoff, max_backoff)
                        )

                return last_result or ExecutionResult.fatal(
                    "No response after all retry attempts"
                )

            return async_wrapper

    return decorator
