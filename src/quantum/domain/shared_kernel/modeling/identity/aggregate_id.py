from dataclasses import dataclass
from uuid import UUID

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class AggregateId(ValueObject):
    """
    Globally unique aggregate identity.
    """

    value: UUID

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvariantViolation("AggregateId must be UUID")

    def __str__(self) -> str:
        return str(self.value)
