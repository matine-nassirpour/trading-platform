from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.capital_management.allocation.capital_fraction import (
    CapitalFraction,
)
from quantum.domain.capital_management.allocation.risk_budget_slice import (
    RiskBudgetSlice,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CapitalBudgetSnapshot(ValueObject):
    """
    Immutable snapshot of already consumed reservation capacity.

    Invariants:
    - used_capital_fraction is optional, but if present: 0 < value <= 1
    - used_risk_budget is optional, but if present: 0 < value <= 1
    - remaining capacity is never negative
    """

    used_capital_fraction: CapitalFraction | None
    used_risk_budget: RiskBudgetSlice | None

    def _validate_semantics(self) -> None:
        if self.used_capital_fraction is not None and not isinstance(
            self.used_capital_fraction, CapitalFraction
        ):
            raise InvariantViolation("used_capital_fraction invalid")

        if self.used_risk_budget is not None and not isinstance(
            self.used_risk_budget, RiskBudgetSlice
        ):
            raise InvariantViolation("used_risk_budget invalid")

        if self.remaining_capital_fraction() < Decimal("0"):
            raise InvariantViolation(
                "used_capital_fraction must not exceed total capital capacity"
            )

        if self.remaining_risk_budget() < Decimal("0"):
            raise InvariantViolation(
                "used_risk_budget must not exceed total risk budget capacity"
            )

    def remaining_capital_fraction(self) -> Decimal:
        used = (
            self.used_capital_fraction.value
            if self.used_capital_fraction is not None
            else Decimal("0")
        )
        return Decimal("1") - used

    def remaining_risk_budget(self) -> Decimal:
        used = (
            self.used_risk_budget.value
            if self.used_risk_budget is not None
            else Decimal("0")
        )
        return Decimal("1") - used
