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
    - optionally load stream from a given sequence
    - append pending envelopes atomically
    - assign official sequence and recorded_at
    """

    async def append(
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

    async def load_stream(
        self,
        stream_id: str,
        *,
        from_sequence: EventSequence | None = None,
        limit: int | None = None,
    ) -> list[RecordedEventEnvelope]:
        """
        Load persisted events for a stream.

        Contract:
        - If from_sequence is None, load from the beginning.
        - If from_sequence is provided, return events strictly after it.
        - If limit is provided, return at most limit events.
        - Events must be returned in strictly increasing sequence order.
        """
        raise NotImplementedError

    async def current_sequence(self, stream_id: str) -> EventSequence:
        """
        Returns last known sequence for a stream.
        """
        raise NotImplementedError
