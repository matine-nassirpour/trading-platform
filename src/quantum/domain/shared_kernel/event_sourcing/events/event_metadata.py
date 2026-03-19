from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
from quantum.domain.shared_kernel.event_sourcing.events.causation_id import CausationId
from quantum.domain.shared_kernel.event_sourcing.events.correlation_id import (
    CorrelationId,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class EventMetadata(ValueObject):
    """
    Metadata attached to every event.

    This layer captures execution context, not business meaning.
    """

    actor_id: ActorId
    correlation_id: CorrelationId
    causation_id: CausationId

    def _validate(self) -> None:
        if not isinstance(self.actor_id, ActorId):
            raise InvariantViolation("Invalid ActorId")

        if not isinstance(self.correlation_id, CorrelationId):
            raise InvariantViolation("Invalid CorrelationId")

        if not isinstance(self.causation_id, CausationId):
            raise InvariantViolation("Invalid CausationId")
