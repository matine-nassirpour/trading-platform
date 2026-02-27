from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class PendingEventEnvelope(ValueObject):
    """
    Application-layer event candidate.

    Not yet persisted.
    Has NO sequence.
    """

    id: EventId

    occurred_at: EpochMs
    recorded_at: EpochMs

    event: BaseEvent

    metadata: EventMetadata

    def _validate(self) -> None:
        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventEnvelope requires EventId")

        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires occurred_at: EpochMs")

        if not isinstance(self.recorded_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires recorded_at: EpochMs")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("EventEnvelope requires BaseEvent")

        if not isinstance(self.metadata, EventMetadata):
            raise InvariantViolation("EventEnvelope requires EventMetadata")
