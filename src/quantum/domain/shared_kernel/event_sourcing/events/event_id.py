from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation

_NIL_UUID = UUID(int=0)


@dataclass(frozen=True, slots=True)
class EventId(ValueObject):
    """
    Globally unique, immutable event identifier.

    UUID(0) is reserved as the NIL event (before the first real event).
    """

    value: UUID

    def _validate(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvariantViolation("EventId must wrap a UUID")

    @staticmethod
    def nil() -> EventId:
        return EventId(_NIL_UUID)
