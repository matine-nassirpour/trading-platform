"""
Retry Policy — Application Logic
────────────────────────────────────────────────────────────────────
Encapsulates the decision logic determining whether an operation should
be retried, based on domain-level execution results or technical failures.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult


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
        if exc:
            return isinstance(exc, self.RETRIABLE_EXCEPTIONS)
        if isinstance(result, ExecutionResult):
            return result.code in self.RETRIABLE_CODES
        return False
