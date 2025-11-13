from __future__ import annotations

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
from quantum.application.orchestrator.ports.broadcaster_port import (
    ExecutionBroadcasterPort,
)
from quantum.application.orchestrator.ports.orchestrator_port import (
    ExecutionOrchestratorPort,
)
from quantum.application.orchestrator.ports.router_port import ExecutionRouterPort
from quantum.application.ports.outbound.observability_port import ObservabilityPort
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionOrchestrator(ExecutionOrchestratorPort):
    """
    High-level orchestration façade.

    Pure responsibilities:
        - build orchestration context (correlation ID + metadata)
        - decide if request is broadcast or single-channel
        - delegate to router or broadcaster
        - return a clean result type

    Non-responsibilities (delegated to subsystems):
        - routing logic  →   ExecutionRouter
        - broadcast logic → ExecutionBroadcaster
        - health & scoring → HealthService
        - eventing/logging/tracing → handled externally
        - retry / resilience  → caller or router level
    """

    def __init__(
        self,
        *,
        router: ExecutionRouterPort,
        broadcaster: ExecutionBroadcasterPort,
        broadcast_policy: (
            callable[[list[ExecutionChannel]], list[ExecutionChannel]] | None
        ) = None,
        observability: ObservabilityPort,
    ) -> None:
        self._router = router
        self._broadcaster = broadcaster
        self._broadcast_policy = broadcast_policy
        self._obs = observability

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def _new_context(
        self, metadata: dict[str, str] | None = None
    ) -> OrchestrationContext:
        """Create a new orchestration context with unique correlation ID."""
        cid = self._obs.ensure_correlation_id()
        return OrchestrationContext.start_new(
            correlation_id=cid,
            metadata=metadata or {},
        )

    def _select_targets(
        self,
        channels: list[ExecutionChannel],
    ) -> list[ExecutionChannel] | None:
        """Return channels selected for broadcasting, or None for single-mode."""
        if self._broadcast_policy is None:
            return None
        return self._broadcast_policy(channels)

    # --------------------------------------------------------------------------
    # Public orchestration API
    # --------------------------------------------------------------------------
    async def execute_order(
        self,
        ctx: OrchestrationContext | None,
        request: OrderRequest,
    ) -> ExecutionResult | BroadcastResult:
        ctx = ctx or self._new_context()
        channels = self._router.list_channels()
        targets = self._select_targets(channels)

        if targets is not None:
            return await self._broadcaster.broadcast_order(ctx, targets, request)

        return await self._router.route_order(ctx, request)

    async def execute_check(
        self,
        ctx: OrchestrationContext | None,
        request: CheckRequest,
    ) -> ExecutionResult | BroadcastResult:
        ctx = ctx or self._new_context()
        channels = self._router.list_channels()
        targets = self._select_targets(channels)

        if targets is not None:
            return await self._broadcaster.broadcast_check(ctx, targets, request)

        return await self._router.route_check(ctx, request)

    async def execute_positions(
        self,
        ctx: OrchestrationContext | None,
        request: QueryRequest,
    ) -> ExecutionResult:
        ctx = ctx or self._new_context()
        return await self._router.route_positions(ctx, request)

    async def execute_orders(
        self,
        ctx: OrchestrationContext | None,
        request: QueryRequest,
    ) -> ExecutionResult:
        ctx = ctx or self._new_context()
        return await self._router.route_orders(ctx, request)
