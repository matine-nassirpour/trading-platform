from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


@runtime_checkable
class EventPublisher(Protocol):
    """
    Publishes domain events to the outside world.
    """

    @abstractmethod
    def publish(self, events: Iterable[EventEnvelope]) -> None:
        raise NotImplementedError
