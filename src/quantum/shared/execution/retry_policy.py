"""
Retry Policy — Pure Decision Logic
──────────────────────────────────────────────────────────────────────────────
Encapsulates the logic for deciding if an operation should be retried.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult


class RetryPolicy(Protocol):
    """Interface defining a retry decision engine."""

    def should_retry(self, result: Any | None, exc: Exception | None) -> bool: ...


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Default Implementation                                                      │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class DefaultRetryPolicy:
    """
    Default retry strategy for execution and network layers.
    - Retries only on transient or recoverable errors.
    - Ignores deterministic business errors.
    """

    RETRIABLE_EXCEPTIONS = (TimeoutError, ConnectionError, asyncio.TimeoutError)
    RETRIABLE_CODES = {
        ExecutionCode.INTERNAL_FAIL_TIMEOUT,
        ExecutionCode.SERVER_BUSY,
        ExecutionCode.TRADE_TIMEOUT,
        ExecutionCode.NO_CONNECTION,
    }

    def should_retry(self, result: Any | None, exc: Exception | None) -> bool:
        if exc:
            return isinstance(exc, self.RETRIABLE_EXCEPTIONS)
        if isinstance(result, ExecutionResult):
            return result.code in self.RETRIABLE_CODES
        return False
