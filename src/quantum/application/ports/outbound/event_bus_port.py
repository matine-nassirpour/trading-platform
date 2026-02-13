from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


@runtime_checkable
class EventBusPort(Protocol):
    """
    Abstraction of an asynchronous event bus.
    Provides a clean interface decoupled from any transport (asyncio, ZeroMQ, Kafka...).
    """

    def initialize(self) -> None:
        """Initialize underlying resources (no-op for in-memory backends)."""
        ...

    def close(self) -> None:
        """Gracefully shut down the event bus (optional cleanup)."""
        ...

    def publish(self, events: list[EventEnvelope]) -> None: ...
