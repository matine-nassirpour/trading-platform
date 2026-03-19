from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from quantum.application.shared.eventing.pending_event_envelope import (
    PendingEventEnvelope,
)
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class EventStore(Protocol):
    """
    EventStore port.

    Responsibilities:
    - load persisted stream by storage stream id
    - append pending envelopes atomically
    - assign official sequence and recorded_at
    """

    @abstractmethod
    def append(
        self,
        *,
        stream_id: str,
        events: Sequence[PendingEventEnvelope],
        expected_version: EventSequence,
    ) -> list[RecordedEventEnvelope]:
        """
        Persist events and assign sequential sequence numbers.

        Returns the persisted envelopes with updated sequence.
        Must raise ConcurrencyError on version conflict.
        """
        raise NotImplementedError

    @abstractmethod
    def load_stream(self, stream_id: str) -> list[RecordedEventEnvelope]:
        raise NotImplementedError

    @abstractmethod
    def current_sequence(self, stream_id: str) -> EventSequence:
        """
        Returns last known sequence for a stream.
        """
        raise NotImplementedError
