from collections.abc import Iterable

from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


def persist_events_transactionally(
    *,
    stream_id: str,
    events: Iterable[BaseEvent],
    store: EventStore,
    outbox: OutboxRepository,
    uow: UnitOfWork,
    ids: IdGenerator,
    clock: Clock,
    actor: str,
    expected_version: EventSequence | None = None,
) -> list[EventEnvelope]:

    envelopes: list[EventEnvelope] = []

    for event in events:
        envelopes.append(
            EventEnvelope(
                id=ids.new_event_id(),
                sequence=EventSequence.initial(),
                occurred_at=clock.now_epoch_ms(),
                recorded_at=clock.now_epoch_ms(),
                event=event,
                metadata=EventMetadata(
                    actor_id=ActorId(actor),
                    correlation_id=ids.new_correlation_id(),
                    causation_id=CausationId.root(),
                ),
            )
        )

    persisted = store.append(
        stream_id=stream_id,
        events=envelopes,
        expected_version=expected_version,
    )

    outbox.add(persisted)

    # --- Register post-commit dispatcher
    def publish_after_commit() -> None:
        # publication done asynchronously by infrastructure dispatcher
        pass

    uow.after_commit(publish_after_commit)

    return persisted
