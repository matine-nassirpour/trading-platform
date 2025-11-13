from __future__ import annotations

import asyncio

from typing import Any, Protocol

from quantum.application.contracts.execution_code import ExecutionCode
from quantum.application.contracts.execution_result import ExecutionResult


class RetryPolicy(Protocol):
    """Interface defining a retry decision engine."""

    def should_retry(self, result: Any | None, exc: Exception | None) -> bool: ...


class DefaultRetryPolicy:
    """Default retry strategy for transient or recoverable errors."""

    RETRIABLE_EXCEPTIONS = (TimeoutError, ConnectionError, asyncio.TimeoutError)
    RETRIABLE_CODES = {
        ExecutionCode.INTERNAL_FAIL_TIMEOUT,
        ExecutionCode.SERVER_BUSY,
        ExecutionCode.TRADE_TIMEOUT,
        ExecutionCode.NO_CONNECTION,
    }

    def should_retry(self, result: Any | None, exc: Exception | None) -> bool:
        """
        Decide whether to retry based on result or exception.
        Returns True if the operation is considered transient.
        """
        # Exception-based decision (technical fault)
        if exc is not None:
            return isinstance(exc, self.RETRIABLE_EXCEPTIONS)

        # Result-based decision (business fault)
        if isinstance(result, ExecutionResult):
            return result.code in self.RETRIABLE_CODES

        # Default: non-retryable
        return False
