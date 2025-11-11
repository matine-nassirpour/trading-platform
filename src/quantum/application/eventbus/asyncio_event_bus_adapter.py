from __future__ import annotations

import asyncio
import logging

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from quantum.application.eventbus.event_bus_port import EventBusPort

logger = logging.getLogger(__name__)


class AsyncioEventBusAdapter(EventBusPort):
    """
    In-memory asynchronous event bus using asyncio.Queue and publish/subscribe pattern.

    Designed for:
        - In-process event routing
        - Low-latency signaling
        - Testing and local orchestration

    Safe for multitask coroutine environments (not thread-safe by design).
    """

    def __init__(self) -> None:
        self._subscribers: dict[
            str, list[Callable[[dict[str, Any]], Awaitable[None]]]
        ] = defaultdict(list)
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self._running = False
        self._loop_task: asyncio.Task[None] | None = None

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Register a coroutine handler for the specified topic."""
        self._subscribers[topic].append(handler)
        logger.debug("[EventBus] Subscribed handler to topic=%s", topic)

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Enqueue an event for asynchronous delivery."""
        if not self._running:
            raise RuntimeError(
                "AsyncioEventBusAdapter must be started before publishing."
            )
        await self._queue.put((topic, payload))
        logger.debug("[EventBus] Published event topic=%s payload=%s", topic, payload)

    async def start(self) -> None:
        """Start the event dispatch loop."""
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        logger.info("[EventBus] Started event loop")

    async def close(self) -> None:
        """Stop the event loop gracefully."""
        self._running = False
        if self._loop_task:
            await self._loop_task
        logger.info("[EventBus] Closed")

    # --------------------------------------------------------------------------
    # Internal loop
    # --------------------------------------------------------------------------
    async def _run_loop(self) -> None:
        """Continuously dispatch events to registered subscribers."""
        while self._running:
            try:
                topic, payload = await self._queue.get()
                handlers = self._subscribers.get(topic, [])
                if not handlers:
                    logger.debug("[EventBus] No subscribers for topic=%s", topic)
                    continue

                for handler in handlers:
                    asyncio.create_task(self._safe_invoke(handler, payload))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("[EventBus] Loop error: %s", e)

    @staticmethod
    async def _safe_invoke(
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        payload: dict[str, Any],
    ) -> None:
        """Safely invoke a subscriber handler with error isolation."""
        try:
            await handler(payload)
        except Exception as e:
            logger.exception("[EventBus] Handler error: %s", e)
