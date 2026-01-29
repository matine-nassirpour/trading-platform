from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CausationId(ValueObject):
    """
    Identifies the direct cause of an event.

    Typical usage:
        - Event B has causation_id = Event A.id
        - Allows full causal chain reconstruction
    """

    value: EventId

    def _validate(self) -> None:
        if not isinstance(self.value, EventId):
            raise InvariantViolation("CausationId must wrap EventId")

    @staticmethod
    def from_event_id(event_id: EventId) -> CausationId:
        return CausationId(event_id)

    @staticmethod
    def root() -> CausationId:
        """
        Used for genesis / system-originated events.
        """
        return CausationId(EventId.nil())

    def __str__(self) -> str:
        return str(self.value.value)
