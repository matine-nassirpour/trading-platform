from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
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
        clock: Clock,
        ids: IdGenerator,
        actor: str,
    ) -> None:
        self._store = store
        self._aggregate_type = aggregate_type
        self._clock = clock
        self._ids = ids
        self._actor = ActorId(actor)

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
        domain_events: Iterable[BaseEvent],
        correlation_id: CorrelationId | None = None,
        causation_id: CausationId | None = None,
    ) -> list[EventEnvelope]:
        """
        Persist domain events atomically with strict concurrency control.
        """

        now = self._clock.now_epoch_ms()
        correlation_id = correlation_id or self._ids.new_correlation_id()
        causation_id = causation_id or CausationId.root()

        envelopes: list[EventEnvelope] = []

        for event in domain_events:
            envelopes.append(
                EventEnvelope(
                    id=self._ids.new_event_id(),
                    sequence=EventSequence.initial(),
                    occurred_at=now,
                    recorded_at=now,
                    event=event,
                    metadata=EventMetadata(
                        actor_id=self._actor,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    ),
                )
            )

        persisted = self._store.append(
            stream_id=stream_id,
            events=envelopes,
            expected_version=expected_version,
        )

        return persisted
