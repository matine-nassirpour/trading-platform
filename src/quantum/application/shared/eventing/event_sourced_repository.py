from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.transaction.event_store import EventStore
from quantum.application.shared.errors.application_error import ApplicationError
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.persisted_event_envelope import (
    PersistedEventEnvelope,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)

A = TypeVar("A", bound=EventSourcedAggregateRoot)


class EventSourcedRepository(Generic[A]):
    """
    Pure Event-Sourced repository.

    Guarantees:
    - Aggregate reconstructed only from EventStore
    - Version derived exclusively from stream
    - No state-based persistence
    - Deterministic rebuild
    """

    __slots__ = ("_store", "_aggregate_type")

    def __init__(
        self,
        *,
        store: EventStore,
        aggregate_type: type[A],
    ) -> None:
        self._store = store
        self._aggregate_type = aggregate_type

    def load(self, stream_id: str) -> tuple[A, EventSequence]:
        """
        Load aggregate from EventStore.
        """

        events: list[PersistedEventEnvelope] = self._store.load_stream(stream_id)

        previous = EventSequence.initial()

        for event in events:
            if event.sequence is None:
                raise ApplicationError("Event without sequence")

            event.sequence.assert_is_next_of(previous)
            previous = event.sequence

        # --- Empty Stream
        if not events:
            aggregate = self._aggregate_type(self._aggregate_type.empty_state())

            return aggregate, previous

        # --- Replay
        aggregate = self._aggregate_type.rehydrate(events=events)

        return aggregate, events[-1].sequence

    def save(
        self,
        *,
        stream_id: str,
        expected_version: EventSequence,
        envelopes: Iterable[PersistedEventEnvelope],
    ) -> list[PersistedEventEnvelope]:
        """
        Persist envelopes atomically.
        """

        persisted = self._store.append(
            stream_id=stream_id,
            events=envelopes,
            expected_version=expected_version,
        )

        previous = expected_version
        for envelope in persisted:
            if envelope.sequence is None:
                raise ApplicationError(
                    f"EventStore returned envelope without sequence assignment "
                    f"(stream_id={stream_id})"
                )

            envelope.sequence.assert_is_next_of(previous)
            previous = envelope.sequence

        return persisted
