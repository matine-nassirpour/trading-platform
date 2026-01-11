from dataclasses import dataclass

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class EventEnvelope(ValueObject):
    """
    Audit-grade event wrapper.

    Guarantees:
    - Global identity
    - Stream ordering
    - Timestamp
    - Payload immutability
    """

    id: EventId
    sequence: EventSequence
    occurred_at: EpochMs
    event: BaseEvent

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate(self) -> None:
        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventEnvelope requires EventId")

        if not isinstance(self.sequence, EventSequence):
            raise InvariantViolation("EventEnvelope requires EventSequence")

        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires EpochMs")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("EventEnvelope requires BaseEvent")
