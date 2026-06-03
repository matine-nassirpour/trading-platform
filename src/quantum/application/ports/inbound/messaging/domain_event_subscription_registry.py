from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from quantum.application.ports.inbound.messaging.domain_event_handler import (
    DomainEventHandler,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


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

    @abstractmethod
    def handlers_for(
        self,
        event_type: type[BaseEvent],
    ) -> Sequence[DomainEventHandler]:
        raise NotImplementedError
