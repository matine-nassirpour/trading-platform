from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class LeverageLimit(NumericValueObject):
    """
    Maximum allowed leverage.

    Example:
        5.0 → 5x leverage
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value <= Decimal("0"):
            raise InvariantViolation("LeverageLimit must be strictly positive")
