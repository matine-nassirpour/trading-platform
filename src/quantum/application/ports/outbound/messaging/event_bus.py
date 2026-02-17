from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope

EventEnvelopeHandler = Callable[[EventEnvelope], None]


@runtime_checkable
class EventBus(Protocol):
    """
    Abstraction of an asynchronous event bus.
    Provides a clean interface decoupled from any transport (asyncio, ZeroMQ, Kafka...).
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize underlying transport resources.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Release resources.
        """
        raise NotImplementedError

    @abstractmethod
    def publish(
        self,
        events: list[EventEnvelope],
    ) -> None:
        """
        Publish events to the bus.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        event_type: type[BaseEvent],
        handler: EventEnvelopeHandler,
    ) -> None:
        """
        Register a handler for a given domain event type.

        Multiple handlers per event type allowed.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(
        self,
        event_type: type[BaseEvent],
        handler: EventEnvelopeHandler,
    ) -> None:
        """
        Remove handler subscription.
        """
        raise NotImplementedError
