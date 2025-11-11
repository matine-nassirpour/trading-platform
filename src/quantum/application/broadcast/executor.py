from __future__ import annotations

import asyncio
import logging

from typing import Any

from quantum.application.broadcast.broadcast_result import BroadcastResult
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.services.execution_service import ExecutionService
from quantum.domain.types.execution_channel import ExecutionChannel

logger = logging.getLogger(__name__)


class BroadcastExecutor:
    """
    Executes orders concurrently across multiple execution channels.
    """

    def __init__(self, services: dict[ExecutionChannel, ExecutionService]) -> None:
        self._services = services

    async def broadcast_order_async(
        self,
        targets: list[ExecutionChannel],
        call: str,
        *args: Any,
        **kwargs: Any,
    ) -> BroadcastResult:
        """
        Execute the given call across all target channels concurrently.
        """

        async def run_single(
            ch: ExecutionChannel,
        ) -> tuple[ExecutionChannel, ExecutionResult]:
            service = self._services[ch]
            fn = getattr(service, call)
            try:
                # Support both sync and async resilient calls
                if asyncio.iscoroutinefunction(fn):
                    result = await fn(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, fn, *args)
                logger.debug("[Broadcast] %s: %s", ch.value, result.code)
                return ch, result
            except Exception as e:
                logger.exception("[Broadcast] %s failed: %s", ch.value, e)
                return ch, ExecutionResult.fatal(str(e))

        results = await asyncio.gather(*(run_single(ch) for ch in targets))
        return BroadcastResult(results=dict(results))
