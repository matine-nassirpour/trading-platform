import uuid

from datetime import UTC, datetime

from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


class EventEnvelopeFactory:
    """
    Deterministic factory responsible for constructing
    fully valid EventEnvelope instances.
    """

    @staticmethod
    def create(
        *,
        event: BaseEvent,
        sequence: EventSequence,
        actor: ActorId,
        correlation: CorrelationId,
        causation: CausationId,
        occurred_at: datetime | None = None,
    ) -> EventEnvelope:

        now = datetime.now(tz=UTC)
        occurred = occurred_at or now

        return EventEnvelope(
            id=EventId(uuid.uuid4()),
            sequence=sequence,
            occurred_at=EpochMs.from_datetime(occurred),
            recorded_at=EpochMs.from_datetime(now),
            event=event,
            metadata=EventMetadata(
                actor_id=actor,
                correlation_id=correlation,
                causation_id=causation,
            ),
        )
