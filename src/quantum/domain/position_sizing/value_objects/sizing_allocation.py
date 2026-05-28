from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SizingCapitalFraction(NumericValueObject):
    """
    Fraction of equity usable by this sizing decision.
    Local to position_sizing.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "sizing_capital_fraction"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("SizingCapitalFraction must be strictly positive")

        if self.value > Decimal("1"):
            raise InvariantViolation("SizingCapitalFraction must not exceed 1")


@dataclass(frozen=True, slots=True)
class SizingRiskBudgetSlice(NumericValueObject):
    """
    Fraction of equity allowed to be risked by this sizing decision.
    Local to position_sizing.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "sizing_risk_budget_slice"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("SizingRiskBudgetSlice must be strictly positive")

        if self.value > Decimal("1"):
            raise InvariantViolation("SizingRiskBudgetSlice must not exceed 1")


@dataclass(frozen=True, slots=True)
class SizingAllocation(ValueObject):
    """
    Position-sizing-local allocation input.

    This is intentionally NOT capital_management.CapitalAllocationIntent.
    """

    capital_fraction: SizingCapitalFraction
    risk_budget: SizingRiskBudgetSlice

    def _validate_semantics(self) -> None:
        if not isinstance(self.capital_fraction, SizingCapitalFraction):
            raise InvariantViolation("SizingAllocation.capital_fraction invalid")

        if not isinstance(self.risk_budget, SizingRiskBudgetSlice):
            raise InvariantViolation("SizingAllocation.risk_budget invalid")

        if self.risk_budget.value > self.capital_fraction.value:
            raise InvariantViolation(
                "SizingAllocation.risk_budget must not exceed capital_fraction"
            )
