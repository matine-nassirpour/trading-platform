from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.execution.retry_policy import should_retry
from quantum.shared.execution.timeout_utils import (
    run_with_timeout_async,
    run_with_timeout_sync,
)
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R", bound=ExecutionResult)

settings = ConfigManager.load()
_DEFAULT_MAX_RETRIES = settings.quantum_exec_retries
_DEFAULT_TIMEOUT = settings.quantum_exec_timeout
_DEFAULT_BACKOFF = settings.quantum_exec_backoff
_DEFAULT_BACKOFF_MAX = settings.quantum_exec_backoff_max


def _compute_backoff(attempt: int, base: float, max_backoff: float) -> float:
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
    Decorator providing retry, timeout enforcement, and exponential backoff.
    Works for both sync and async functions returning ExecutionResult.
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
                    try:
                        result: R = run_with_timeout_sync(
                            func,
                            *args,
                            timeout_sec=timeout_sec,
                            call_name=op_name,
                            **kwargs,
                        )
                        last_result = result

                        if not should_retry(result.code):
                            return result

                        logger.warning(
                            f"[{op_name}] Retryable code {result.code} (attempt {attempt}/{max_retries})"
                        )

                    except TimeoutError as e:
                        logger.error(f"[{op_name}] Timeout: {e}")
                        last_result = ExecutionResult.retryable(str(e))
                    except Exception as e:
                        msg = f"{type(e).__name__}: {e}"
                        logger.exception(
                            f"[{op_name}] Exception on attempt {attempt}: {msg}"
                        )
                        last_result = ExecutionResult.fatal(msg)

                    if attempt < max_retries:
                        time.sleep(_compute_backoff(attempt, base_backoff, max_backoff))

                return last_result or ExecutionResult.fatal(
                    "No result after all retries"
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
                        result: R = await run_with_timeout_async(
                            func,
                            *args,
                            timeout_sec=timeout_sec,
                            call_name=op_name,
                            **kwargs,
                        )
                        last_result = result

                        if not should_retry(result.code):
                            return result

                        logger.warning(
                            f"[{op_name}] Retryable code {result.code} (attempt {attempt}/{max_retries})"
                        )

                    except TimeoutError as e:
                        logger.error(f"[{op_name}] Timeout: {e}")
                        last_result = ExecutionResult.retryable(str(e))
                    except Exception as e:
                        msg = f"{type(e).__name__}: {e}"
                        logger.exception(
                            f"[{op_name}] Exception on attempt {attempt}: {msg}"
                        )
                        last_result = ExecutionResult.fatal(msg)

                    if attempt < max_retries:
                        await asyncio.sleep(
                            _compute_backoff(attempt, base_backoff, max_backoff)
                        )

                return last_result or ExecutionResult.fatal(
                    "No result after all retries"
                )

            return async_wrapper

    return decorator
