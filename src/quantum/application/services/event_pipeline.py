from collections.abc import Iterable

from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


async def persist_and_publish(
    *,
    stream_id: str,
    events: Iterable[BaseEvent],
    store: EventStore,
    bus: EventBusPort,
    ids: IdGenerator,
    clock: Clock,
    actor: str,
) -> list[EventEnvelope]:
    envelopes = []

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

    persisted = store.append(stream_id, envelopes)

    await bus.publish_many(persisted)

    return persisted
