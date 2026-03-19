from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.event_sourcing.events.event_metadata import (
    EventMetadata,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId
from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class PendingEventEnvelope(ValueObject):
    """
    Application-layer event candidate.

    Not yet persisted:
    - no sequence
    - no official recorded_at assigned by EventStore
    """

    aggregate_id: AggregateId
    id: EventId
    occurred_at: EpochMs
    event: BaseEvent
    metadata: EventMetadata

    def _validate(self) -> None:
        if not isinstance(self.aggregate_id, AggregateId):
            raise InvariantViolation("PendingEventEnvelope.aggregate_id is required")

        if not isinstance(self.id, EventId):
            raise InvariantViolation("PendingEventEnvelope.id is required")

        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("PendingEventEnvelope.occurred_at is required")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("PendingEventEnvelope.event is required")

        if not isinstance(self.metadata, EventMetadata):
            raise InvariantViolation("PendingEventEnvelope.metadata is required")
