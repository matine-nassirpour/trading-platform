from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.risk.capital.allocation.capital_fraction import CapitalFraction
from quantum.domain.risk.capital.allocation.risk_budget_slice import RiskBudgetSlice
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CapitalBudgetSnapshot(ValueObject):
    """
    Immutable snapshot of available capacity at the time of booking.

    Represents the state already aggregated by a projection/application service:
    - capital already reserved
    - risk already reserved
    - remaining capacity
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
