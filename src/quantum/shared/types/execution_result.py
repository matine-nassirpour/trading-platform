from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantum.shared.types.execution import ExecutionCode


@dataclass(frozen=True)
class ExecutionResult:
    """
    Immutable result of an execution request.

    Attributes
    ----------
    code : ExecutionCode
        Outcome code (success, error, etc.)
    message : str
        Diagnostic or informational message
    payload : Any | None
        Optional attached data (response, error detail, etc.)
    """

    code: ExecutionCode
    message: str
    payload: Any | None = None

    # ────────────────────────────────
    # Constructors / Factory methods
    # ────────────────────────────────

    @classmethod
    def ok(
        cls, message: str = "success", payload: Any | None = None
    ) -> ExecutionResult:
        """Successful result."""
        return cls(code=ExecutionCode.OK, message=message, payload=payload)

    @classmethod
    def retryable(
        cls, message: str = "transient failure", payload: Any | None = None
    ) -> ExecutionResult:
        """Transient failure that may be retried."""
        return cls(
            code=ExecutionCode.INTERNAL_FAIL_TIMEOUT, message=message, payload=payload
        )

    @classmethod
    def fatal(
        cls, message: str = "fatal error", payload: Any | None = None
    ) -> ExecutionResult:
        """Non-recoverable failure."""
        return cls(code=ExecutionCode.INTERNAL_FAIL, message=message, payload=payload)

    # ────────────────────────────────
    # Helpers
    # ────────────────────────────────

    def succeeded(self) -> bool:
        """Return True if the operation succeeded."""
        return self.code == ExecutionCode.OK

    def failed(self) -> bool:
        """Return True if the operation failed."""
        return not self.succeeded()
