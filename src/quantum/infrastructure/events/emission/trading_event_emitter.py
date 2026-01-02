"""
Trading Event Emitter
─────────────────────
Dedicated application component responsible for publishing domain trading events
through the configured EventBusPort.

Institutional-grade properties:
- Asynchronous, non-blocking publication
- Backpressure with bounded queue
- Graceful startup/shutdown
- Robust error handling with limited retries
- Clean separation of responsibilities (orchestrator produces, emitter publishes)
"""

from __future__ import annotations

import asyncio
import logging
import time

from dataclasses import dataclass
from typing import Final

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.infrastructure.events.emission.event_adapter import adapt_event_for_bus
from quantum.infrastructure.events.emission.event_retry_policy import (
    EventRetryConfig,
    EventRetryPolicy,
)
from quantum.infrastructure.events.mapping.topic_map import map_topic

LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmitterConfig:
    queue_maxsize: int = 2048
    concurrency: int = 4  # number of publisher workers
    shutdown_grace_s: float = 5.0  # wait time for draining


class TradingEventEmitter:
    """
    High-resilience asynchronous event emitter.

    Guarantees:
        - Non-blocking enqueue with bounded backpressure
        - Structured retry via EventRetryPolicy
        - Graceful shutdown under load
    """

    def __init__(
        self,
        event_bus: EventBusPort,
        cfg: EmitterConfig | None = None,
        retry_policy: EventRetryPolicy | None = None,
    ) -> None:
        self._bus = event_bus
        self._cfg = cfg or EmitterConfig()
        self._retry_policy = retry_policy or EventRetryPolicy(EventRetryConfig())
        self._queue: asyncio.Queue[object] = asyncio.Queue(
            maxsize=self._cfg.queue_maxsize
        )
        self._workers: list[asyncio.Task[None]] = []
        self._closing = asyncio.Event()

    # --- Lifecycle ------------------------------------------------------------

    async def start(self) -> None:
        """
        Start background publisher workers.
        Must be awaited once during application bootstrap.
        """
        for i in range(self._cfg.concurrency):
            task = asyncio.create_task(
                self._worker(i), name=f"trading-event-emitter-{i}"
            )
            self._workers.append(task)
        LOGGER.info(
            "[Emitter] started concurrency=%d queue_max=%d",
            self._cfg.concurrency,
            self._cfg.queue_maxsize,
        )

    async def close(self) -> None:
        """
        Graceful shutdown:
        - stop accepting new events,
        - drain queue (bounded by shutdown_grace_s),
        - cancel workers.
        """
        self._closing.set()
        deadline = time.time() + self._cfg.shutdown_grace_s

        # Wait until queue is drained or deadline reached
        while not self._queue.empty() and time.time() < deadline:
            await asyncio.sleep(0.05)

        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        LOGGER.info("[Emitter] closed (remaining=%d)", self._queue.qsize())

    # --- Public API -----------------------------------------------------------

    async def emit(self, event: object) -> None:
        """
        Enqueue an event for asynchronous publication.
        Backpressure: caller will await if queue is full.
        """
        if self._closing.is_set():
            LOGGER.warning(
                "[Emitter] emit called after closing — dropped event=%s", event
            )
            return
        await self._queue.put(event)

    # --- Internal Helpers -----------------------------------------------------

    async def _worker(self, worker_id: int) -> None:
        try:
            while not self._closing.is_set():
                event = await self._queue.get()
                try:
                    await self._publish_with_resilience(event)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            LOGGER.debug("[Emitter] worker-%d cancelled", worker_id)

    async def _publish_with_resilience(self, event: object) -> None:
        """Publish event with retry logic provided by EventRetryPolicy."""
        name, payload = adapt_event_for_bus(event)
        topic = map_topic(name)

        async def publish_once() -> None:
            await self._bus.publish(topic, payload)
            LOGGER.debug("[Emitter] published %s → %s", name, topic)

        await self._retry_policy.execute_with_retry(name, publish_once)
