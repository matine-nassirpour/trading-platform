from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CausationId(ValueObject):
    """
    Identifies the direct cause of an event.

    DOCTRINE:
    - wraps an EventId;
    - CausationId.root() is the canonical sentinel for genesis/system-originated flows;
    - root causation uses EventId.nil() by convention;
    - this DOES NOT mean a recorded event may use EventId.nil() as its own id.
    """

    value: EventId

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, EventId):
            raise InvariantViolation("CausationId must wrap EventId")

    @staticmethod
    def from_event_id(event_id: EventId) -> CausationId:
        return CausationId(event_id)

    @staticmethod
    def root() -> CausationId:
        """
        Canonical root causation sentinel used for genesis/system-originated events.
        """
        return CausationId(EventId.nil())

    def is_root(self) -> bool:
        return self.value.is_nil()

    def __str__(self) -> str:
        return str(self.value.value)
