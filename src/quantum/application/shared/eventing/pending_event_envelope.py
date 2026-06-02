from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.event_sourcing.events.event_metadata import (
    EventMetadata,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


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

    def _validate_semantics(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("aggregate_id", self.aggregate_id, AggregateId),
            ("id", self.id, EventId),
            ("occurred_at", self.occurred_at, EpochMs),
            ("event", self.event, BaseEvent),
            ("metadata", self.metadata, EventMetadata),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"PendingEventEnvelope.{field_name} invalid")
