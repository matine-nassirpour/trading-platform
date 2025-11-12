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

from quantum.application.events.serialization import serialize_event
from quantum.application.events.topic_map import map_topic
from quantum.application.ports.outbound.event_bus_port import EventBusPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmitterConfig:
    queue_maxsize: int = 2048
    concurrency: int = 4  # number of publisher workers
    max_retries: int = 3
    base_backoff_s: float = 0.2
    backoff_cap_s: float = 2.0
    shutdown_grace_s: float = 5.0  # wait time for draining


class TradingEventEmitter:
    """
    Publish domain trading events to the EventBusPort with
    bounded backpressure and robust retry semantics.
    """

    def __init__(
        self, event_bus: EventBusPort, cfg: EmitterConfig | None = None
    ) -> None:
        self._bus = event_bus
        self._cfg = cfg or EmitterConfig()
        self._queue: asyncio.Queue[object] = asyncio.Queue(
            maxsize=self._cfg.queue_maxsize
        )
        self._workers: list[asyncio.Task[None]] = []
        self._closing = asyncio.Event()

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------
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
        logger.info(
            "[Emitter] started with concurrency=%d queue_max=%d",
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

        for t in self._workers:
            t.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("[Emitter] closed (remaining=%d)", self._queue.qsize())

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    async def emit(self, event: object) -> None:
        """
        Enqueue an event for asynchronous publication.
        Backpressure: caller will await if queue is full.
        """
        if self._closing.is_set():
            logger.warning(
                "[Emitter] emit called after closing; dropping event=%s", event
            )
            return
        await self._queue.put(event)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    async def _worker(self, worker_id: int) -> None:
        try:
            while not self._closing.is_set():
                event = await self._queue.get()
                try:
                    await self._publish_with_retry(event)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            # drain on cancellation until queue is empty or closing
            logger.debug("[Emitter] worker-%d cancelled", worker_id)

    async def _publish_with_retry(self, event: object) -> None:
        name, payload = serialize_event(event)
        topic = map_topic(name)

        backoff = self._cfg.base_backoff_s
        for attempt in range(1, self._cfg.max_retries + 1):
            try:
                await self._bus.publish(topic, payload)
                logger.debug("[Emitter] published %s to %s", name, topic)
                return
            except Exception as exc:
                logger.warning(
                    "[Emitter] publish failed (attempt=%d/%d) event=%s exc=%s",
                    attempt,
                    self._cfg.max_retries,
                    name,
                    type(exc).__name__,
                )
                if attempt >= self._cfg.max_retries:
                    logger.error(
                        "[Emitter] giving up event=%s after %d attempts", name, attempt
                    )
                    return
                await asyncio.sleep(min(backoff, self._cfg.backoff_cap_s))
                backoff *= 2.0
