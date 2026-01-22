from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


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
