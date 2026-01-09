from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True)
class RiskBreach:
    kind: RiskBreachKind
    current: ContextualMonetaryAmount
    limit: ContextualMonetaryAmount

    def __post_init__(self) -> None:
        if self.current.context != self.limit.context:
            raise InvariantViolation("RiskBreach MoneyContext mismatch")

        if self.current.value < self.limit.value:
            raise InvariantViolation("Risk breach requires current ≥ limit")
