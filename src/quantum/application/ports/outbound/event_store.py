from abc import ABC, abstractmethod
from collections.abc import Iterable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class EventStore(ABC):
    """
    Application-level contract for event persistence.
    """

    @abstractmethod
    def append(self, events: Iterable[EventEnvelope]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_all(self) -> Iterable[EventEnvelope]:
        raise NotImplementedError

    @abstractmethod
    def load_from_sequence(self, sequence: EventSequence) -> Iterable[EventEnvelope]:
        raise NotImplementedError
