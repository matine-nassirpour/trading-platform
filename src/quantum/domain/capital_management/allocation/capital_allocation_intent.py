from dataclasses import dataclass

from quantum.domain.capital_management.allocation.capital_fraction import (
    CapitalFraction,
)
from quantum.domain.capital_management.allocation.risk_budget_slice import (
    RiskBudgetSlice,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CapitalAllocationIntent(ValueObject):
    """
    Canonical capital allocation envelope for a trading decision.

    This object answers:
        "How much capital AND risk is this decision allowed to consume?"
    """

    capital_fraction: CapitalFraction
    risk_budget: RiskBudgetSlice

    def _validate_semantics(self) -> None:
        if not isinstance(self.capital_fraction, CapitalFraction):
            raise InvariantViolation("Invalid CapitalFraction")

        if not isinstance(self.risk_budget, RiskBudgetSlice):
            raise InvariantViolation("Invalid RiskBudgetSlice")
