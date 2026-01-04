from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskBreach(ValueObject):
    """
    Canonical representation of a risk breach.
    """

    kind: RiskBreachKind
    current: MonetaryValueObject
    limit: MonetaryValueObject

    def _validate(self) -> None:
        if not isinstance(self.kind, RiskBreachKind):
            raise InvariantViolation("RiskBreach must have a valid kind")

        if self.current.currency != self.limit.currency:
            raise InvariantViolation("Risk breach currency mismatch")

        if self.current.value < self.limit.value:
            raise InvariantViolation(
                "RiskBreach current value must exceed or equal limit"
            )
