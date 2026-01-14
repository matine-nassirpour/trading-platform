from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.trading.capital.capital_fraction import CapitalFraction
from quantum.domain.trading.capital.risk_budget_slice import RiskBudgetSlice


@dataclass(frozen=True, slots=True)
class CapitalAllocationIntent(ValueObject):
    """
    Canonical capital allocation envelope for a trading decision.

    This object answers:
        "How much capital AND risk is this decision allowed to consume?"

    IMPORTANT:
    - Declarative, not computed
    - Stable over time
    - Fully auditable
    """

    capital_fraction: CapitalFraction
    risk_budget: RiskBudgetSlice

    def _validate(self) -> None:
        if not isinstance(self.capital_fraction, CapitalFraction):
            raise InvariantViolation("Invalid CapitalFraction")

        if not isinstance(self.risk_budget, RiskBudgetSlice):
            raise InvariantViolation("Invalid RiskBudgetSlice")
