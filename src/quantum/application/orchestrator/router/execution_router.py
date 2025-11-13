from __future__ import annotations

import asyncio
import time

from quantum.application.contracts.execution_operation import ExecutionOperation
from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.orchestrator.allocation.allocation_policy import (
    AllocationPolicy,
)
from quantum.application.orchestrator.context.orchestration_context import (
    OrchestrationContext,
)
from quantum.application.orchestrator.health.health_service import HealthService
from quantum.application.ports.outbound.tracing_port import TracingPort
from quantum.application.services.execution_service import ExecutionService
from quantum.application.services.operation_registry import OPERATION_REGISTRY
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionRouter:
    """Route a request to exactly ONE execution channel.

    Responsibilities:
        - select healthy channels
        - enforce circuit breaker
        - allocate channel via allocation policy
        - delegate to ExecutionService
        - feed back latency & success/failure to HealthService

    The router does not deal with events, broadcasting, or orchestration-wide logic.
    """

    def __init__(
        self,
        *,
        services: dict[ExecutionChannel, ExecutionService],
        health: HealthService,
        allocation_policy: AllocationPolicy,
        observability: TracingPort,
        concurrency_limit: int = 8,
    ) -> None:
        self._services = services
        self._health = health
        self._alloc = allocation_policy
        self._tracing = observability
        self._sem = asyncio.Semaphore(concurrency_limit)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    async def _select_channel(self, ctx: OrchestrationContext) -> ExecutionChannel:
        async with await self._tracing.trace(
            "router.select_channel",
            attributes={
                "correlation_id": ctx.correlation_id,
                "attempt": ctx.attempt,
            },
        ) as span:

            channels = list(self._services.keys())
            await span.set_attribute("candidate_channels", [c.value for c in channels])

            healthy = await self._health.get_healthy_channels(channels)
            candidates = healthy if healthy else channels

            await span.set_attribute("healthy_channels", [c.value for c in healthy])
            await span.set_attribute("eligible_channels", [c.value for c in candidates])

            channel = self._alloc.select_channel(candidates)
            await span.set_attribute("selected_channel", channel.value)

            return channel

    async def _run_service_call(
        self,
        ctx: OrchestrationContext,
        channel: ExecutionChannel,
        op: ExecutionOperation,
        request,
    ) -> ExecutionResult:

        async with await self._tracing.trace(
            "router.service_call",
            attributes={
                "correlation_id": ctx.correlation_id,
                "operation": op.name,
                "channel": channel.value,
            },
        ) as span:

            service = self._services[channel]
            fn = OPERATION_REGISTRY[op]

            loop = asyncio.get_running_loop()
            start = time.perf_counter()

            try:
                result: ExecutionResult = await loop.run_in_executor(
                    None, lambda: fn(service, request)
                )
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000.0

                await span.set_attribute("duration_ms", duration_ms)

                # hybrid failure reporting
                await self._tracing.record_failure(
                    f"router.service_call.{op.name}",
                    exc,
                    attributes={
                        "channel": channel.value,
                        "duration_ms": duration_ms,
                        "correlation_id": ctx.correlation_id,
                    },
                )

                # feed health
                await self._health.record_failure(channel, latency_ms=duration_ms)

                raise

            # Success path
            latency_ms = (time.perf_counter() - start) * 1000.0
            await span.set_attribute("duration_ms", latency_ms)
            await span.set_attribute("result_success", result.succeeded())

            # feed health metrics
            if result.succeeded():
                await self._health.record_success(channel, latency_ms=latency_ms)
            else:
                await self._health.record_failure(channel, latency_ms=latency_ms)

            return result

    # --------------------------------------------------------------------------
    # Public routing API
    # --------------------------------------------------------------------------
    async def route_order(
        self,
        ctx: OrchestrationContext,
        request: OrderRequest,
    ) -> ExecutionResult:
        async with self._sem:
            channel = await self._select_channel(ctx)
            return await self._run_service_call(
                ctx, channel, ExecutionOperation.SEND_ORDER, request
            )

    async def route_check(
        self,
        ctx: OrchestrationContext,
        request: CheckRequest,
    ) -> ExecutionResult:
        async with self._sem:
            channel = await self._select_channel(ctx)
            return await self._run_service_call(
                ctx, channel, ExecutionOperation.CHECK_ORDER, request
            )

    async def route_positions(
        self,
        ctx: OrchestrationContext,
        request: QueryRequest,
    ) -> ExecutionResult:
        async with self._sem:
            channel = await self._select_channel(ctx)
            return await self._run_service_call(
                ctx, channel, ExecutionOperation.GET_POSITIONS, request
            )

    async def route_orders(
        self,
        ctx: OrchestrationContext,
        request: QueryRequest,
    ) -> ExecutionResult:
        async with self._sem:
            channel = await self._select_channel(ctx)
            return await self._run_service_call(
                ctx, channel, ExecutionOperation.GET_ORDERS, request
            )

    # --------------------------------------------------------------------------
    # Introspection
    # --------------------------------------------------------------------------
    def list_channels(self) -> list[ExecutionChannel]:
        return list(self._services.keys())
