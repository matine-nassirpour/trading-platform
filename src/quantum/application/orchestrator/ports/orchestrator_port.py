from __future__ import annotations

from typing import Protocol

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.orchestrator.context.orchestration_context import (
    OrchestrationContext,
)


class ExecutionOrchestratorPort(Protocol):
    """High-level orchestration façade.

    Combines:
        - routing for single-channel flows
        - broadcasting for multichannel flows

    This port is ALWAYS async-only.
    """

    async def execute_order(
        self,
        ctx: OrchestrationContext | None,
        request: OrderRequest,
    ) -> ExecutionResult | BroadcastResult: ...

    async def execute_check(
        self,
        ctx: OrchestrationContext | None,
        request: CheckRequest,
    ) -> ExecutionResult | BroadcastResult: ...

    async def execute_positions(
        self,
        ctx: OrchestrationContext | None,
        request: QueryRequest,
    ) -> ExecutionResult: ...

    async def execute_orders(
        self,
        ctx: OrchestrationContext | None,
        request: QueryRequest,
    ) -> ExecutionResult: ...
