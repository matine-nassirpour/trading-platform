from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)

DomainEventHandler = Callable[[RecordedEventEnvelope], None]


@runtime_checkable
class DomainEventSubscriptionRegistry(Protocol):
    """
    Registry of in-process domain event handlers.

    Responsibility:
    - Maintain handler subscriptions only.
    """

    @abstractmethod
    def subscribe(
        self,
        event_type: type[BaseEvent],
        handler: DomainEventHandler,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(
        self,
        event_type: type[BaseEvent],
        handler: DomainEventHandler,
    ) -> None:
        raise NotImplementedError
