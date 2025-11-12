"""
Execution Orchestrator
──────────────────────
High-level orchestrator managing multichannel execution routing and broadcasting.

Responsibilities:
    - Route execution requests to the appropriate ExecutionService (per channel)
    - Handle health-based fail-over and retry delegation
    - Support broadcast (multi-execution) mode across channels
    - Publish structured lifecycle events via EventBusPort
    - Maintain independence from domain and infrastructure layers

Design principles:
    - Pure Application-layer construct (depends only on ports & policies)
    - Asynchronous event publication via EventBusPort
    - Fully compliant with Clean Architecture (no infrastructure leakage)
"""

from __future__ import annotations

import asyncio
import logging
import time

from typing import Any

from quantum.application.broadcast.broadcast_policy import BroadcastPolicy
from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.broadcast.executor import BroadcastExecutor
from quantum.application.contracts.execution_code import is_success
from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.orchestrator.policies.allocation_policy import AllocationPolicy
from quantum.application.orchestrator.policies.health_policy import (
    ChannelHealth,
    HealthPolicy,
)
from quantum.application.orchestrator.ports.orchestrator_port import (
    ExecutionOrchestratorPort,
)
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.execution_service import ExecutionService
from quantum.domain.events.trading.v1.order_fill_event import OrderFillEvent
from quantum.domain.events.trading.v1.order_reject_event import OrderRejectEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.types.execution_channel import ExecutionChannel

logger = logging.getLogger(__name__)


class ExecutionOrchestrator(ExecutionOrchestratorPort):
    """
    Core application orchestrator coordinating multi-channel execution.
    """

    def __init__(
        self,
        *,
        services: dict[ExecutionChannel, ExecutionService],
        allocation_policy: AllocationPolicy,
        health_policy: HealthPolicy,
        event_bus: EventBusPort | None = None,
        broadcast_policy: BroadcastPolicy | None = None,
    ) -> None:
        self._services = services
        self._alloc = allocation_policy
        self._health = health_policy
        self._event_bus = event_bus
        self._broadcast_policy = broadcast_policy
        self._broadcaster = BroadcastExecutor(services)

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def _select_channel(self) -> ExecutionChannel:
        """Select a healthy channel using the allocation policy."""
        all_channels = list(self._services.keys())
        healthy = self._health.get_healthy_channels(all_channels)
        candidates = healthy if healthy else all_channels
        channel = self._alloc.select_channel(candidates)
        logger.debug(
            "ExecutionOrchestrator selected channel=%s (healthy=%s)",
            channel,
            channel in healthy,
        )
        return channel

    def _get_service(self, channel: ExecutionChannel) -> ExecutionService:
        """Retrieve the service bound to a specific channel."""
        return self._services[channel]

    def _update_health(
        self, channel: ExecutionChannel, result: ExecutionResult
    ) -> None:
        """Update channel health metrics based on last execution result."""
        healthy = is_success(result.code)
        self._health.update_health(
            ChannelHealth(
                channel=channel,
                is_healthy=healthy,
                latency_ms=None,  # enriched later via observability integration
                last_check_epoch_s=time.time(),
            )
        )

    async def _publish_event(self, event: Any) -> None:
        """Publish an event asynchronously if an EventBus is configured."""
        if not self._event_bus:
            return

        try:
            # Compatible with BaseEvent-based events
            if hasattr(event, "event_name") and hasattr(event, "to_payload"):
                await self._event_bus.publish(
                    event.event_name,
                    event.to_payload(),
                )
            else:
                # Fallback: raw dictionary or string event
                event_name = getattr(event, "event_name", type(event).__name__)
                payload = event if isinstance(event, dict) else {"value": str(event)}
                await self._event_bus.publish(event_name, payload)

        except Exception as exc:
            logger.warning(
                "[Orchestrator] Failed to publish event %s: %s",
                getattr(event, "event_name", type(event).__name__),
                exc,
            )

    # --------------------------------------------------------------------------
    # Unified entrypoints (sync, optional broadcast)
    # --------------------------------------------------------------------------
    def send_order(self, request: OrderRequest) -> ExecutionResult | BroadcastResult:
        """Dispatch an order request to a single or multiple execution channels."""
        if self._broadcast_policy:
            targets = self._broadcast_policy.select_targets(list(self._services.keys()))
            logger.info(
                "[Orchestrator] Broadcasting order to %d channels: %s",
                len(targets),
                [c.value for c in targets],
            )
            result = asyncio.run(
                self._broadcaster.broadcast_order_async(targets, "send_order", request)
            )
            asyncio.run(self._publish_event(OrderSubmitEvent(symbol=request.symbol)))
            return result

        channel = self._select_channel()
        service = self._get_service(channel)
        result = service.send_order(request)
        self._update_health(channel, result)

        # Publish appropriate lifecycle event
        event = (
            OrderFillEvent(symbol=request.symbol)
            if result.succeeded()
            else OrderRejectEvent(symbol=request.symbol, detail=result.message)
        )
        asyncio.run(self._publish_event(event))

        return result

    def check_order(self, request: CheckRequest) -> ExecutionResult | BroadcastResult:
        """Verify order validity before execution."""
        if self._broadcast_policy:
            targets = self._broadcast_policy.select_targets(list(self._services.keys()))
            logger.info(
                "[Orchestrator] Broadcasting check to %d channels: %s",
                len(targets),
                [c.value for c in targets],
            )
            result = asyncio.run(
                self._broadcaster.broadcast_order_async(targets, "check_order", request)
            )
            return result

        channel = self._select_channel()
        service = self._get_service(channel)
        result = service.check_order(request)
        self._update_health(channel, result)
        return result

    def get_positions(self, request: QueryRequest) -> ExecutionResult:
        """Query open positions from the selected healthy channel."""
        channel = self._select_channel()
        service = self._get_service(channel)
        result = service.get_positions(request)
        self._update_health(channel, result)
        return result

    def get_orders(self, request: QueryRequest) -> ExecutionResult:
        """Query open orders from the selected healthy channel."""
        channel = self._select_channel()
        service = self._get_service(channel)
        result: ExecutionResult = service.get_orders(request)  # type: ignore[call-arg]
        self._update_health(channel, result)
        return result
