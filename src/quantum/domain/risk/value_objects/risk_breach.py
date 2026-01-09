from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskBreach(ValueObject):
    """
    Canonical representation of a detected risk breach.
    """

    kind: RiskBreachKind
    current: ContextualMonetaryAmount
    limit: ContextualMonetaryAmount

    def _validate(self) -> None:
        if not isinstance(self.kind, RiskBreachKind):
            raise InvariantViolation("RiskBreach requires a RiskBreachKind")

        if not isinstance(self.current, ContextualMonetaryAmount):
            raise InvariantViolation(
                "RiskBreach requires a current ContextualMonetaryAmount"
            )

        if not isinstance(self.limit, ContextualMonetaryAmount):
            raise InvariantViolation(
                "RiskBreach requires a limit ContextualMonetaryAmount"
            )

        if self.current.context != self.limit.context:
            raise InvariantViolation("RiskBreach MoneyContext mismatch")

        if self.current.value < self.limit.value:
            raise InvariantViolation("Risk breach requires current ≥ limit")
