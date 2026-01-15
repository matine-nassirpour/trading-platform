from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class EventEnvelope(ValueObject):
    """
    Audit-grade domain event envelope.

    This object represents the act of recording a Domain Event
    into an immutable event stream.
    """

    id: EventId
    sequence: EventSequence
    recorded_at: EpochMs
    event: BaseEvent

    def _validate(self) -> None:
        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventEnvelope requires EventId")

        if not isinstance(self.sequence, EventSequence):
            raise InvariantViolation("EventEnvelope requires EventSequence")

        if not isinstance(self.recorded_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires recorded_at: EpochMs")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("EventEnvelope requires BaseEvent")

        if self.sequence.is_initial():
            raise InvariantViolation("EventEnvelope.sequence must be >= 1")
