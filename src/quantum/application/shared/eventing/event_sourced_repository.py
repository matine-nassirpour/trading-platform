from collections.abc import Sequence
from typing import Generic, TypeVar

from quantum.application.ports.outbound.transaction.event_store import EventStore
from quantum.application.shared.errors.application_error import ApplicationError
from quantum.application.shared.eventing.pending_event_envelope import (
    PendingEventEnvelope,
)
from quantum.application.shared.eventing.stream_name_resolver import StreamNameResolver
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.event_sourcing.state.aggregate_state import (
    AggregateState,
)
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId

ID = TypeVar("ID", bound=AggregateId)
S = TypeVar("S", bound=AggregateState)
A = TypeVar("A", bound=EventSourcedAggregateRoot)


class EventSourcedRepository(Generic[ID, S, A]):
    """
    Strict event-sourced repository.

    Guarantees:
    - Aggregate identity remains typed in application core
    - Storage stream name is derived, never invented ad hoc
    - Empty aggregate reconstruction preserves canonical identity
    - Version is derived exclusively from persisted stream
    - No state-based persistence
    """

    __slots__ = ("_store", "_aggregate_type", "_stream_resolver")

    def __init__(
        self,
        *,
        store: EventStore,
        aggregate_type: type[A],
        stream_resolver: StreamNameResolver[ID],
    ) -> None:
        self._store = store
        self._aggregate_type = aggregate_type
        self._stream_resolver = stream_resolver

    async def load(
        self,
        *,
        aggregate_id: ID,
        from_sequence: EventSequence | None = None,
        limit: int | None = None,
    ) -> tuple[A, EventSequence]:
        """
        Load aggregate from EventStore using its typed aggregate identity.

        By default, loads the full stream.
        For advanced use cases, partial loading can be requested explicitly.
        """

        if not isinstance(aggregate_id, AggregateId):
            raise ApplicationError("load() requires a typed AggregateId")

        stream_id = self._stream_resolver.resolve(aggregate_id)

        events = await self._store.load_stream(
            stream_id,
            from_sequence=from_sequence,
            limit=limit,
        )

        previous = from_sequence or EventSequence.initial()

        for event in events:
            event.sequence.assert_is_next_of(previous)
            previous = event.sequence

            if event.aggregate_id != aggregate_id:
                raise ApplicationError(
                    f"EventStore returned mixed aggregate identity for stream "
                    f"'{stream_id}': expected '{aggregate_id}', got '{event.aggregate_id}'"
                )

        # --- Empty Stream
        if not events:
            aggregate = self._aggregate_type(
                aggregate_id,
                self._aggregate_type.uninitialized_state(),
            )
            return aggregate, previous

        if from_sequence is not None:
            raise ApplicationError(
                "Partial aggregate rehydration is not allowed without snapshot support"
            )

        # --- Replay
        aggregate = self._aggregate_type.rehydrate(
            events=events,
            aggregate_id=aggregate_id,
        )

        return aggregate, events[-1].sequence

    async def save(
        self,
        *,
        aggregate_id: ID,
        expected_version: EventSequence,
        envelopes: Sequence[PendingEventEnvelope],
    ) -> list[RecordedEventEnvelope]:
        """
        Persist already-materialized envelopes atomically.
        """

        if not isinstance(aggregate_id, AggregateId):
            raise ApplicationError("save() requires a typed AggregateId")

        stream_id = self._stream_resolver.resolve(aggregate_id)

        for envelope in envelopes:
            if envelope.aggregate_id != aggregate_id:
                raise ApplicationError(
                    f"Envelope aggregate_id mismatch for stream '{stream_id}'"
                )

        persisted = await self._store.append(
            stream_id=stream_id,
            events=envelopes,
            expected_version=expected_version,
        )

        previous = expected_version

        for envelope in persisted:
            if envelope.aggregate_id != aggregate_id:
                raise ApplicationError(
                    f"EventStore returned persisted envelope with mismatched "
                    f"aggregate_id for stream '{stream_id}'"
                )

            envelope.sequence.assert_is_next_of(previous)
            previous = envelope.sequence

        return persisted
