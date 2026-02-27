from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.application.shared.eventing.pending_event_envelope import (
    PendingEventEnvelope,
)
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.persisted_event_envelope import (
    PersistedEventEnvelope,
)


@runtime_checkable
class EventStore(Protocol):
    """
    Event store with strict sequencing and optimistic concurrency.
    """

    @abstractmethod
    def append(
        self,
        stream_id: str,
        events: Iterable[PendingEventEnvelope],
        expected_version: EventSequence,
    ) -> list[PersistedEventEnvelope]:
        """
        Persist events and assign sequential sequence numbers.

        Returns the persisted envelopes with updated sequence.
        Must raise ConcurrencyError on version conflict.
        """
        raise NotImplementedError

    @abstractmethod
    def load_stream(self, stream_id: str) -> list[PersistedEventEnvelope]:
        raise NotImplementedError

    @abstractmethod
    def current_sequence(self, stream_id: str) -> EventSequence:
        """
        Returns last known sequence for a stream.
        """
        raise NotImplementedError
