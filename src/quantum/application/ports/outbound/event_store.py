from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


@runtime_checkable
class EventStore(Protocol):
    """
    Application-level contract for event persistence.
    """

    @abstractmethod
    def append(self, events: Iterable[EventEnvelope]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_stream(self, stream_id: str) -> Iterable[EventEnvelope]:
        raise NotImplementedError

    @abstractmethod
    def load_all(self) -> Iterable[EventEnvelope]:
        raise NotImplementedError

    @abstractmethod
    def load_from_sequence(self, sequence: EventSequence) -> Iterable[EventEnvelope]:
        raise NotImplementedError
