from __future__ import annotations

from typing import Protocol

from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.orchestrator.context.orchestration_context import (
    OrchestrationContext,
)
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionRouterPort(Protocol):
    """Port for routing a single execution request to exactly one channel.

    The router:
        - selects a healthy channel via allocation policy,
        - verifies circuit breaker availability,
        - delegates to the execution service bound to the channel.
    """

    async def route_order(
        self,
        ctx: OrchestrationContext,
        request: OrderRequest,
    ) -> ExecutionResult: ...

    async def route_check(
        self,
        ctx: OrchestrationContext,
        request: CheckRequest,
    ) -> ExecutionResult: ...

    async def route_positions(
        self,
        ctx: OrchestrationContext,
        request: QueryRequest,
    ) -> ExecutionResult: ...

    async def route_orders(
        self,
        ctx: OrchestrationContext,
        request: QueryRequest,
    ) -> ExecutionResult: ...

    def list_channels(self) -> list[ExecutionChannel]:
        """Return the list of channels handled by the router."""
        ...
