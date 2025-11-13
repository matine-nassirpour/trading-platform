from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_request import CheckRequest, OrderRequest
from quantum.application.orchestrator.context.orchestration_context import (
    OrchestrationContext,
)
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionBroadcasterPort(Protocol):
    """Port for multichannel broadcasts."""

    async def broadcast_order(
        self,
        ctx: OrchestrationContext,
        channels: Sequence[ExecutionChannel],
        request: OrderRequest,
    ) -> BroadcastResult: ...

    async def broadcast_check(
        self,
        ctx: OrchestrationContext,
        channels: Sequence[ExecutionChannel],
        request: CheckRequest,
    ) -> BroadcastResult: ...
