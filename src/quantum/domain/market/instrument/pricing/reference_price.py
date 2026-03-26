from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class ReferencePrice(NumericValueObject):
    """
    Non-executable price used as a decision or market snapshot reference.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "reference_price"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value < Decimal("0"):
            raise InvariantViolation("ReferencePrice must be non-negative")
