from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DealId(ValueObject):
    value: int

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvariantViolation("DealId must be a strict int (not bool)")
        if self.value < 1:
            raise InvariantViolation("DealId must be ≥ 1")
