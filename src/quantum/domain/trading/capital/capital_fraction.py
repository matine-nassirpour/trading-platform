from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class CapitalFraction(NumericValueObject):
    """
    Fraction of total capital allocated to a decision.

    Semantics:
    - 0 < fraction ≤ 1
    - Declarative (NOT computed)
    - Independent of price / volume / leverage
    """

    def _validate(self) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("CapitalFraction must be strictly positive")

        if self.value > Decimal("1"):
            raise InvariantViolation("CapitalFraction must not exceed 1.0")
