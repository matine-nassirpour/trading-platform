from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.transaction.event_store import EventStore
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
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

    def __init__(
        self,
        *,
        store: EventStore,
        aggregate_type: type[A],
    ) -> None:
        self._store = store
        self._aggregate_type = aggregate_type

    def load(self, stream_id: str) -> tuple[A | None, EventSequence]:
        events: list[EventEnvelope] = self._store.load_stream(stream_id)

        if not events:
            return None, EventSequence.initial()

        aggregate = self._aggregate_type.rehydrate(
            events=events,
            empty_state=self._aggregate_type.empty_state(),
        )

        version = events[-1].sequence
        return aggregate, version

    def save(
        self,
        *,
        stream_id: str,
        expected_version: EventSequence,
        envelopes: Iterable[EventEnvelope],
    ) -> list[EventEnvelope]:
        """
        Persist pre-wrapped event envelopes atomically.
        """

        persisted = self._store.append(
            stream_id=stream_id,
            events=envelopes,
            expected_version=expected_version,
        )

        return persisted
