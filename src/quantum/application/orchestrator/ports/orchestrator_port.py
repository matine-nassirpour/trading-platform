from typing import Protocol

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult


class ExecutionOrchestratorPort(Protocol):
    """
    Abstract interface for orchestrating execution across multiple channels.
    Implementations must ensure concurrency safety and health-aware routing.
    """

    # --------------------------------------------------------------------------
    # Asynchronous API (primary, production-grade)
    # --------------------------------------------------------------------------
    async def send_order(
        self, request: OrderRequest
    ) -> ExecutionResult | BroadcastResult:
        """Asynchronously dispatch an order request (single or broadcast)."""
        ...

    async def check_order(
        self, request: CheckRequest
    ) -> ExecutionResult | BroadcastResult:
        """Asynchronously verify order validity before execution."""
        ...

    async def get_positions(self, request: QueryRequest) -> ExecutionResult:
        """Asynchronously query open positions from an execution channel."""
        ...

    async def get_orders(self, request: QueryRequest) -> ExecutionResult:
        """Asynchronously query open orders from an execution channel."""
        ...

    # --------------------------------------------------------------------------
    # Transitional synchronous API (legacy compatibility)
    # --------------------------------------------------------------------------
    def send_order_sync(
        self, request: OrderRequest
    ) -> ExecutionResult | BroadcastResult:
        """Synchronous wrapper for send_order (temporary)."""
        ...

    def check_order_sync(
        self, request: CheckRequest
    ) -> ExecutionResult | BroadcastResult:
        """Synchronous wrapper for check_order (temporary)."""
        ...

    def get_positions_sync(self, request: QueryRequest) -> ExecutionResult:
        """Synchronous wrapper for get_positions (temporary)."""
        ...

    def get_orders_sync(self, request: QueryRequest) -> ExecutionResult:
        """Synchronous wrapper for get_orders (temporary)."""
        ...
