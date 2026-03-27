from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_NIL_UUID = UUID(int=0)


@dataclass(frozen=True, slots=True)
class EventId(ValueObject):
    """
    Globally unique, immutable event identifier.

    SPECIAL CASE:
    UUID(0) is reserved as the NIL event identifier sentinel.

    DOCTRINE:
    - EventId.nil() is allowed as a domain-level sentinel value;
    - it may be used for root causation / pre-first-event semantics;
    - it MUST NEVER be used as the identifier of a recorded event.
    """

    value: UUID

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvariantViolation("EventId must wrap a UUID")

    def is_nil(self) -> bool:
        """
        Returns True if this EventId is the reserved NIL sentinel.
        """
        return self.value == _NIL_UUID

    @staticmethod
    def nil() -> EventId:
        """
        Reserved sentinel event identifier.

        IMPORTANT:
        This value is valid as a sentinel only.
        It must never be assigned to a persisted / recorded event.
        """
        return EventId(_NIL_UUID)

    def __str__(self) -> str:
        return str(self.value)
