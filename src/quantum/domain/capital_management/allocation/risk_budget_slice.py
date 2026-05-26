from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
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

    @classmethod
    def nominal_type(cls) -> str:
        return "risk_budget_slice"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("RiskBudgetSlice must be strictly positive")

        if self.value > Decimal("1"):
            raise InvariantViolation("RiskBudgetSlice must not exceed 1.0")
