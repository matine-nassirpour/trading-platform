from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.event_sourcing.events.event_metadata import (
    EventMetadata,
)
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RecordedEventEnvelope(ValueObject):
    """
    Domain-grade immutable event record.

    This represents an event that is OFFICIALLY RECORDED in the event stream.
    """

    aggregate_id: AggregateId
    id: EventId

    sequence: EventSequence

    occurred_at: EpochMs  # When the business fact occurred
    recorded_at: EpochMs  # When the system persisted the event

    event: BaseEvent
    metadata: EventMetadata

    def _validate_types(self) -> None:
        if not isinstance(self.aggregate_id, AggregateId):
            raise InvariantViolation("AggregateId is required")

        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventId is required")

        if not isinstance(self.sequence, EventSequence):
            raise InvariantViolation("EventSequence is required")

        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("EpochMs is required")

        if not isinstance(self.recorded_at, EpochMs):
            raise InvariantViolation("EpochMs is required")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("BaseEvent is required")

        if not isinstance(self.metadata, EventMetadata):
            raise InvariantViolation("EventMetadata is required")

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.sequence.is_initial():
            raise InvariantViolation("RecordedEventEnvelope.sequence must be >= 1")

        if self.recorded_at.value < self.occurred_at.value:
            raise InvariantViolation(
                "RecordedEventEnvelope.recorded_at must be >= occurred_at"
            )
