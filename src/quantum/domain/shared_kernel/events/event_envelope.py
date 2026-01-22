from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class EventEnvelope(ValueObject):
    """
    Audit-grade domain event envelope.

    Represents the act of recording a Domain Event into an immutable event stream.
    """

    id: EventId
    sequence: EventSequence
    occurred_at: EpochMs  # When the business fact occurred
    recorded_at: EpochMs  # When the system persisted the event

    event: BaseEvent
    metadata: EventMetadata

    def _validate_types(self) -> None:
        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventEnvelope requires EventId")

        if not isinstance(self.sequence, EventSequence):
            raise InvariantViolation("EventEnvelope requires EventSequence")

        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires occurred_at: EpochMs")

        if not isinstance(self.recorded_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires recorded_at: EpochMs")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("EventEnvelope requires BaseEvent")

        if not isinstance(self.metadata, EventMetadata):
            raise InvariantViolation("EventEnvelope requires EventMetadata")

    def _validate_sequence(self) -> None:
        if self.sequence.is_initial():
            raise InvariantViolation("EventEnvelope.sequence must be >= 1")

    def _validate_temporal_consistency(self) -> None:
        if self.recorded_at.value < self.occurred_at.value:
            raise InvariantViolation("EventEnvelope.recorded_at must be >= occurred_at")

    def _validate(self) -> None:
        self._validate_types()
        self._validate_sequence()
        self._validate_temporal_consistency()
