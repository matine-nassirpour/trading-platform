from dataclasses import dataclass

from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class IntegrationHeaders(ValueObject):
    """
    Transport-level headers required for any integration event.
    """

    message_id: str
    event_name: str
    event_version: int

    correlation_id: CorrelationId
    causation_id: CausationId
    actor_id: ActorId

    source: str
    tenant: str | None = None
    environment: str | None = None
    schema_ref: str | None = None

    def _validate(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise Exception("Invalid CorrelationId")

        if not isinstance(self.causation_id, CausationId):
            raise Exception("Invalid CausationId")

        if not isinstance(self.actor_id, ActorId):
            raise Exception("Invalid ActorId")
