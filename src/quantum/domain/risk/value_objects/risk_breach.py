from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskBreach(ValueObject):
    """
    Canonical representation of a risk breach.

    Properties:
    - Purely descriptive
    - No arithmetic
    - Currency-consistent
    """

    kind: RiskBreachKind
    current: MonetaryAmount
    limit: MonetaryAmount

    def _validate(self) -> None:
        if not isinstance(self.kind, RiskBreachKind):
            raise InvariantViolation("RiskBreach must have a valid kind")

        if not isinstance(self.current, MonetaryAmount):
            raise InvariantViolation("RiskBreach current must be a MonetaryAmount")

        if not isinstance(self.limit, MonetaryAmount):
            raise InvariantViolation("RiskBreach limit must be a MonetaryAmount")

        if self.current.currency != self.limit.currency:
            raise InvariantViolation("Risk breach currency mismatch")

        # Semantic invariant:
        # breach implies current >= limit (or > depending on policy upstream)
        if self.current.value < self.limit.value:
            raise InvariantViolation(
                "RiskBreach current value must exceed or equal limit"
            )
