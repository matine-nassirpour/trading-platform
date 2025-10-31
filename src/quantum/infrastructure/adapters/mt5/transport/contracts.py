"""
Execution Function Contracts
──────────────────────────────────────────────────────────────────────────────
Defines the formal callable interface (protocol) used by all execution
gateways (MT5, FIX, simulator, etc.).
"""

from collections.abc import Callable
from typing import Any, Protocol

from quantum.application.contracts.execution_result import ExecutionResult
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionFunctionProtocol(Protocol):
    """
    Formal callable interface for execution gateways.

    Implementations must execute a trading API call (e.g. MT5 order_send)
    under a fully instrumented, fault-tolerant context and return
    an `ExecutionResult` instance.
    """

    def __call__(
        self,
        call: str,
        func: Callable[..., Any],
        *args: Any,
        channel: ExecutionChannel | None = None,
        **kwargs: Any,
    ) -> ExecutionResult: ...
