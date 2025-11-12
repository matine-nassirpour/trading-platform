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
from quantum.application.events.trading_event_emitter import TradingEventEmitter
from quantum.application.orchestrator.policies.allocation_policy import AllocationPolicy
from quantum.application.orchestrator.policies.health_policy import (
    ChannelHealth,
    HealthPolicy,
)
from quantum.application.orchestrator.ports.orchestrator_port import (
    ExecutionOrchestratorPort,
)
from quantum.application.services.execution_service import ExecutionService
from quantum.domain.events.trading.v1.order_fill_event import OrderFillEvent
from quantum.domain.events.trading.v1.order_reject_event import OrderRejectEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.types.execution_channel import ExecutionChannel

logger = logging.getLogger(__name__)


class AsyncExecutionOrchestrator(ExecutionOrchestratorPort):
    """
    Fully asynchronous orchestrator coordinating multichannel execution.
    Suitable for high-throughput desks running under a persistent event loop.
    """

    def __init__(
        self,
        *,
        services: dict[ExecutionChannel, ExecutionService],
        allocation_policy: AllocationPolicy,
        health_policy: HealthPolicy,
        event_emitter: TradingEventEmitter,
        broadcast_policy: BroadcastPolicy | None = None,
        concurrency_limit: int = 8,
    ) -> None:
        self._services = services
        self._alloc = allocation_policy
        self._health = health_policy
        self._emitter = event_emitter
        self._broadcast_policy = broadcast_policy
        self._broadcaster = BroadcastExecutor(services)
        self._sem = asyncio.Semaphore(concurrency_limit)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _select_channel(self) -> ExecutionChannel:
        """Select a healthy channel using the allocation policy."""
        all_channels = list(self._services.keys())
        healthy = self._health.get_healthy_channels(all_channels)
        candidates = healthy if healthy else all_channels
        channel = self._alloc.select_channel(candidates)
        logger.debug("Selected channel=%s (healthy=%s)", channel, channel in healthy)
        return channel

    def _get_service(self, channel: ExecutionChannel) -> ExecutionService:
        """Retrieve the service bound to a specific channel."""
        return self._services[channel]

    def _update_health(
        self, channel: ExecutionChannel, result: ExecutionResult
    ) -> None:
        """Update channel health metrics based on last execution result."""
        self._health.update_health(
            ChannelHealth(
                channel=channel,
                is_healthy=is_success(result.code),
                latency_ms=None,  # enriched later via observability integration
                last_check_epoch_s=time.time(),
            )
        )

    # --------------------------------------------------------------------------
    # Async orchestration API
    # --------------------------------------------------------------------------
    async def send_order(
        self, request: OrderRequest
    ) -> ExecutionResult | BroadcastResult:
        """Asynchronously dispatch an order to one or more execution channels."""
        async with self._sem:  # prevent overload under high concurrency
            if self._broadcast_policy:
                targets = self._broadcast_policy.select_targets(
                    list(self._services.keys())
                )
                logger.info(
                    "[Orchestrator] Broadcasting order to %d channels: %s",
                    len(targets),
                    [c.value for c in targets],
                )
                result = await self._broadcaster.broadcast_order_async(
                    targets, "send_order", request
                )
                await self._emitter.emit(OrderSubmitEvent(symbol=request.symbol))
                return result

            channel = self._select_channel()
            service = self._get_service(channel)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, service.send_order, request)
            self._update_health(channel, result)

            event = (
                OrderFillEvent(symbol=request.symbol)
                if result.succeeded()
                else OrderRejectEvent(symbol=request.symbol, detail=result.message)
            )
            await self._emitter.emit(event)
            return result

    async def check_order(
        self, request: CheckRequest
    ) -> ExecutionResult | BroadcastResult:
        async with self._sem:
            if self._broadcast_policy:
                targets = self._broadcast_policy.select_targets(
                    list(self._services.keys())
                )
                result = await self._broadcaster.broadcast_order_async(
                    targets, "check_order", request
                )
                return result

            channel = self._select_channel()
            service = self._get_service(channel)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, service.check_order, request)
            self._update_health(channel, result)
            return result

    async def get_positions(self, request: QueryRequest) -> ExecutionResult:
        async with self._sem:
            channel = self._select_channel()
            service = self._get_service(channel)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, service.get_positions, request)
            self._update_health(channel, result)
            return result

    async def get_orders(self, request: QueryRequest) -> ExecutionResult:
        async with self._sem:
            channel = self._select_channel()
            service = self._get_service(channel)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, service.get_orders, request)
            self._update_health(channel, result)
            return result

    # --------------------------------------------------------------------------
    # Optional synchronous wrappers for legacy code
    # --------------------------------------------------------------------------
    def send_order_sync(
        self, request: OrderRequest
    ) -> ExecutionResult | BroadcastResult:
        return asyncio.run(self.send_order(request))

    def check_order_sync(
        self, request: CheckRequest
    ) -> ExecutionResult | BroadcastResult:
        return asyncio.run(self.check_order(request))

    def get_positions_sync(self, request: QueryRequest) -> ExecutionResult:
        return asyncio.run(self.get_positions(request))

    def get_orders_sync(self, request: QueryRequest) -> ExecutionResult:
        return asyncio.run(self.get_orders(request))
