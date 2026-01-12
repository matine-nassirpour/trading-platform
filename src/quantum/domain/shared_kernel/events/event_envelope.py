from dataclasses import dataclass
from typing import Any

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
    Audit-grade domain event envelope.

    This object represents the act of recording a Domain Event
    into an immutable event stream.

    Semantic guarantees:
    - id            → global identity of the record
    - sequence      → strict ordering within a stream
    - recorded_at   → when THIS SYSTEM recorded the event
    - event         → the pure, atemporal domain fact

    IMPORTANT:
    The Domain Event itself carries NO temporal information.
    All time lives in the envelope.
    """

    id: EventId
    sequence: EventSequence
    recorded_at: EpochMs
    event: BaseEvent

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: Any) -> None:
        if not isinstance(self.id, EventId):
            raise InvariantViolation("EventEnvelope requires EventId")

        if not isinstance(self.sequence, EventSequence):
            raise InvariantViolation("EventEnvelope requires EventSequence")

        if not isinstance(self.recorded_at, EpochMs):
            raise InvariantViolation("EventEnvelope requires recorded_at: EpochMs")

        if not isinstance(self.event, BaseEvent):
            raise InvariantViolation("EventEnvelope requires BaseEvent")
