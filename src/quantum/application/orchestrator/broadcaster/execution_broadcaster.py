from __future__ import annotations

import asyncio
import time

from collections.abc import Sequence

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_operation import ExecutionOperation
from quantum.application.contracts.execution_request import CheckRequest, OrderRequest
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.orchestrator.context.orchestration_context import (
    OrchestrationContext,
)
from quantum.application.orchestrator.health.health_service import HealthService
from quantum.application.ports.outbound.tracing_port import TracingPort
from quantum.application.services.execution_service import ExecutionService
from quantum.application.services.operation_registry import OPERATION_REGISTRY
from quantum.domain.types.execution_channel import ExecutionChannel


class ExecutionBroadcaster:
    """Execute the same request across multiple channels in parallel.

    Responsibilities:
        - run all calls concurrently,
        - track per-channel latency & success,
        - update health service accordingly,
        - aggregate results via BroadcastResult.
    """

    def __init__(
        self,
        *,
        services: dict[ExecutionChannel, ExecutionService],
        health: HealthService,
        observability: TracingPort,
    ) -> None:
        self._services = services
        self._health = health
        self._tracing = observability

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    async def _run_one(
        self,
        ctx: OrchestrationContext,
        channel: ExecutionChannel,
        op: ExecutionOperation,
        request,
    ) -> tuple[ExecutionChannel, ExecutionResult]:

        async with await self._tracing.trace(
            "broadcaster.run_one",
            attributes={
                "op": op.name,
                "channel": channel.value,
                "correlation_id": ctx.correlation_id,
                "attempt": ctx.attempt,
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

                await self._tracing.record_failure(
                    f"broadcaster.run_one.{op.name}",
                    exc,
                    attributes={
                        "channel": channel.value,
                        "duration_ms": duration_ms,
                        "correlation_id": ctx.correlation_id,
                    },
                )

                await self._health.record_failure(channel, latency_ms=duration_ms)
                raise

            # Normal success/failure path
            latency_ms = (time.perf_counter() - start) * 1000.0
            await span.set_attribute("duration_ms", latency_ms)
            await span.set_attribute("result_success", result.succeeded())

            if result.succeeded():
                await self._health.record_success(channel, latency_ms=latency_ms)
            else:
                await self._health.record_failure(channel, latency_ms=latency_ms)

            return channel, result

    # --------------------------------------------------------------------------
    # Broadcast APIs
    # --------------------------------------------------------------------------
    async def broadcast_order(
        self,
        ctx: OrchestrationContext,
        channels: Sequence[ExecutionChannel],
        request: OrderRequest,
    ) -> BroadcastResult:

        async with await self._tracing.trace(
            "broadcaster.broadcast_order",
            attributes={
                "correlation_id": ctx.correlation_id,
                "attempt": ctx.attempt,
                "channels": [c.value for c in channels],
            },
        ):
            tasks = [
                self._run_one(ctx, c, ExecutionOperation.SEND_ORDER, request)
                for c in channels
            ]
            results = await asyncio.gather(*tasks)
            return BroadcastResult.from_results(results)

    async def broadcast_check(
        self,
        ctx: OrchestrationContext,
        channels: Sequence[ExecutionChannel],
        request: CheckRequest,
    ) -> BroadcastResult:

        async with await self._tracing.trace(
            "broadcaster.broadcast_check",
            attributes={
                "correlation_id": ctx.correlation_id,
                "attempt": ctx.attempt,
                "channels": [c.value for c in channels],
            },
        ):
            tasks = [
                self._run_one(ctx, c, ExecutionOperation.CHECK_ORDER, request)
                for c in channels
            ]
            results = await asyncio.gather(*tasks)
            return BroadcastResult.from_results(results)
