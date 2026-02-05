from collections.abc import Awaitable, Callable
from typing import Any, Protocol


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

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish an event payload to all subscribers of the given topic."""
        ...

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Register an asynchronous handler for a given topic."""
        ...
