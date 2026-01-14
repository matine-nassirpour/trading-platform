from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class RiskBudgetSlice(NumericValueObject):
    """
    Fraction of the total risk budget consumed by a decision.

    Examples:
    - 0.01 → 1% of total allowed risk
    - 0.05 → aggressive risk usage

    This is NOT monetary.
    """

    def _validate(self) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("RiskBudgetSlice must be strictly positive")

        if self.value > Decimal("1"):
            raise InvariantViolation("RiskBudgetSlice must not exceed 1.0")
