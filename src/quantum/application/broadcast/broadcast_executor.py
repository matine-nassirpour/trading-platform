from __future__ import annotations

import asyncio
import logging

from typing import Any

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort
from quantum.application.resilience.resilience_policy import (
    ResilienceConfig,
    resilient_async_call,
)
from quantum.application.resilience.retry_policy import RetryPolicy
from quantum.application.services.execution_service import ExecutionService
from quantum.domain.types.execution_channel import ExecutionChannel

logger = logging.getLogger(__name__)


class BroadcastExecutor:
    """
    Executes broadcast calls concurrently across multiple execution channels
    with full resilience integration (timeouts, retries, and fault isolation).

    Design goals:
    - Fault-tolerant concurrent execution
    - Resilient calls per service via ResiliencePolicy
    - Compatible with asyncio event loop and backpressure control
    - Safe for integration into orchestrators and event-driven systems
    """

    def __init__(
        self,
        services: dict[ExecutionChannel, ExecutionService],
        *,
        timeout_runner: TimeoutRunnerPort,
        retry_policy: RetryPolicy | None = None,
        cfg: ResilienceConfig | None = None,
        concurrency_limit: int = 8,
    ) -> None:
        self._services = services
        self._timeout_runner = timeout_runner
        self._retry_policy = retry_policy
        self._cfg = cfg
        self._sem = asyncio.Semaphore(concurrency_limit)

    # --------------------------------------------------------------------------
    # Core Broadcast Logic
    # --------------------------------------------------------------------------
    async def broadcast_order_async(
        self,
        targets: list[ExecutionChannel],
        call: str,
        *args: Any,
        **kwargs: Any,
    ) -> BroadcastResult:
        """
        Execute a broadcast call concurrently across multiple channels
        with integrated timeout and retry semantics.
        """

        async def run_single(
            ch: ExecutionChannel,
        ) -> tuple[ExecutionChannel, ExecutionResult]:
            service = self._services[ch]
            fn = getattr(service, call)

            @resilient_async_call(
                timeout_runner=self._timeout_runner,
                policy=self._retry_policy,
                cfg=self._cfg,
            )
            async def safe_call() -> ExecutionResult:
                try:
                    # Handle both sync and async service functions
                    if asyncio.iscoroutinefunction(fn):
                        result = await fn(*args, **kwargs)
                    else:
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(None, fn, *args)
                    return result
                except Exception as e:
                    logger.exception("[Broadcast] %s.%s failed: %s", ch.value, call, e)
                    return ExecutionResult.fatal(str(e))

            try:
                async with self._sem:
                    result = await safe_call()
                    logger.debug(
                        "[Broadcast] %s.%s completed with code=%s",
                        ch.value,
                        call,
                        result.code,
                    )
                    return ch, result
            except Exception as exc:
                logger.exception(
                    "[Broadcast] %s.%s resilience layer failure: %s",
                    ch.value,
                    call,
                    exc,
                )
                return ch, ExecutionResult.fatal(str(exc))

        results = await asyncio.gather(
            *(run_single(ch) for ch in targets), return_exceptions=False
        )
        return BroadcastResult(results=dict(results))

    # --------------------------------------------------------------------------
    # Optional Sync Wrapper (for legacy contexts)
    # --------------------------------------------------------------------------
    def broadcast_order_sync(
        self,
        targets: list[ExecutionChannel],
        call: str,
        *args: Any,
        **kwargs: Any,
    ) -> BroadcastResult:
        """
        Synchronous wrapper for compatibility with blocking contexts.
        """
        return asyncio.run(self.broadcast_order_async(targets, call, *args, **kwargs))
