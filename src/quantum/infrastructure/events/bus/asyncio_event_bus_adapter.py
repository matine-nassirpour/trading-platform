from __future__ import annotations

import asyncio
import logging

from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any, Final

from quantum.application.ports.outbound.event_bus_port import EventBusPort

LOGGER: Final = logging.getLogger(__name__)


class AsyncioEventBusAdapter(EventBusPort):
    """
    Asyncio-based in-memory EventBus implementation.

    This adapter provides a lightweight, high-performance event bus for local
    asynchronous communication within a single process.

    Design goals:
    - Non-blocking, fully async publish/subscribe operations
    - Concurrency-safe registration and publication
    - Structured logging and graceful error isolation per subscriber
    - Predictable shutdown and deterministic behavior
    - Seamless future migration to distributed backends (ZeroMQ, Kafka, NATS)
    """

    def __init__(self) -> None:
        self._subscribers: defaultdict[
            str, list[Callable[[dict[str, Any]], Awaitable[None]]]
        ] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._closed = asyncio.Event()
        self._shutdown_flag = False

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------
    async def initialize(self) -> None:
        """Initialize the event bus runtime (no-op for asyncio)."""
        LOGGER.info("[EventBus] Initialized asyncio in-memory event bus.")

    async def close(self) -> None:
        """Gracefully shut down the event bus."""
        async with self._lock:
            if self._shutdown_flag:
                return
            self._shutdown_flag = True
            self._subscribers.clear()
            self._closed.set()
        LOGGER.info("[EventBus] Asyncio bus closed — no further publications allowed.")

    # --------------------------------------------------------------------------
    # Subscription management
    # --------------------------------------------------------------------------
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
        Register an asynchronous handler for a given topic.

        Handlers are stored per-topic and executed concurrently on publish().
        """
        async with self._lock:
            if self._shutdown_flag:
                raise RuntimeError(
                    f"[EventBus] Cannot subscribe after shutdown: {topic}"
                )
            if handler in self._subscribers[topic]:
                LOGGER.warning(
                    "[EventBus] Duplicate subscription ignored for topic '%s'", topic
                )
                return
            self._subscribers[topic].append(handler)
            LOGGER.debug(
                "[EventBus] Subscribed handler=%s to topic=%s",
                handler.__qualname__,
                topic,
            )

    async def unsubscribe(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Unregister a previously subscribed handler."""
        async with self._lock:
            handlers = self._subscribers.get(topic)
            if not handlers:
                return
            with suppress(ValueError):
                handlers.remove(handler)
                LOGGER.debug(
                    "[EventBus] Unsubscribed handler=%s from topic=%s",
                    handler.__qualname__,
                    topic,
                )
            if not handlers:
                del self._subscribers[topic]

    # --------------------------------------------------------------------------
    # Publishing logic
    # --------------------------------------------------------------------------
    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """
        Publish an event asynchronously to all registered subscribers for the topic.

        Each handler executes concurrently in its own asyncio task.
        Exceptions are isolated and logged individually.
        """
        if self._shutdown_flag:
            LOGGER.warning("[EventBus] Publish ignored after shutdown (%s)", topic)
            return

        async with self._lock:
            subscribers = list(self._subscribers.get(topic, []))

        if not subscribers:
            LOGGER.debug("[EventBus] No subscribers for topic '%s'", topic)
            return

        LOGGER.debug(
            "[EventBus] Publishing topic='%s' to %d subscriber(s)",
            topic,
            len(subscribers),
        )

        tasks = [
            asyncio.create_task(self._safe_invoke(handler, topic, payload))
            for handler in subscribers
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    @staticmethod
    async def _safe_invoke(
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        topic: str,
        payload: dict[str, Any],
    ) -> None:
        """Safely invoke an event handler with structured error logging."""
        try:
            await handler(payload)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            LOGGER.error(
                "[EventBus] Handler error — topic=%s handler=%s exc=%s",
                topic,
                handler.__qualname__,
                exc,
                exc_info=True,
                extra={
                    "attrs": {
                        "topic": topic,
                        "handler": handler.__qualname__,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                },
            )

    # --------------------------------------------------------------------------
    # Introspection
    # --------------------------------------------------------------------------
    def get_subscribers(self, topic: str) -> list[str]:
        """Return a list of subscriber handler names for a given topic."""
        return [h.__qualname__ for h in self._subscribers.get(topic, [])]

    def is_closed(self) -> bool:
        """Return True if the event bus has been closed."""
        return self._shutdown_flag
