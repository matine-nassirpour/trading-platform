from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


@runtime_checkable
class EventBusPort(Protocol):
    """
    Abstraction of an asynchronous event bus.
    Provides a clean interface decoupled from any transport (asyncio, ZeroMQ, Kafka...).
    """

    async def initialize(self) -> None:
        """Initialize underlying resources (no-op for in-memory backends)."""
        ...

    async def close(self) -> None:
        """Gracefully shut down the event bus (optional cleanup)."""
        ...

    async def publish(self, envelope: EventEnvelope) -> None: ...

    async def publish_many(self, envelopes: Iterable[EventEnvelope]) -> None:
        """
        Default implementation may loop,
        but infrastructures can optimize atomically.
        """
        for env in envelopes:
            await self.publish(env)
