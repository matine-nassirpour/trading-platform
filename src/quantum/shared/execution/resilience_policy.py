import functools
import logging
import os
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from quantum.shared.execution.retry_policy import should_retry
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R", bound=ExecutionResult)

# Defaults (configurable via .env)
_DEFAULT_MAX_RETRIES = int(os.getenv("QUANTUM_EXEC_RETRIES", "3"))
_DEFAULT_TIMEOUT = float(os.getenv("QUANTUM_EXEC_TIMEOUT", "5.0"))
_DEFAULT_BACKOFF = float(os.getenv("QUANTUM_EXEC_BACKOFF", "0.5"))
_DEFAULT_BACKOFF_MAX = float(os.getenv("QUANTUM_EXEC_BACKOFF_MAX", "5.0"))


def resilient_call(
    op_name: str,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    timeout_sec: float = _DEFAULT_TIMEOUT,
    base_backoff: float = _DEFAULT_BACKOFF,
    max_backoff: float = _DEFAULT_BACKOFF_MAX,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator providing retry, timeout, exponential backoff and tracing
    around any ExecutionResult-returning function.

    Example:
    --------
    @resilient_call("send_order")
    def send_order(self, request: OrderRequest) -> ExecutionResult:
        ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
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

                    # Retryable error
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
                        payload=None,
                    )

                elapsed = time.time() - start
                if elapsed > timeout_sec:
                    logger.error(
                        f"[{op_name}] Timeout exceeded ({elapsed:.2f}s > {timeout_sec}s)",
                        extra={"attrs": {"attempt": attempt}},
                    )
                    last_result = ExecutionResult.fatal("Operation timeout")

                # Backoff before next attempt
                backoff = min(base_backoff * (2 ** (attempt - 1)), max_backoff)
                if attempt < max_retries:
                    time.sleep(backoff)

            # All retries exhausted
            return last_result or ExecutionResult.fatal(
                "No response after all retry attempts"
            )

        return wrapper

    return decorator
