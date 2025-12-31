from dataclasses import dataclass
from typing import Literal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.money import Money


@dataclass(frozen=True)
class RiskBreach(ValueObject):
    """
    Canonical representation of a risk breach.
    """

    kind: Literal["drawdown", "notional", "daily_loss"]
    current: Money
    limit: Money

    def _validate(self) -> None:
        if self.current.currency != self.limit.currency:
            raise InvariantViolation("Risk breach currency mismatch")

        if self.current.value < self.limit.value:
            raise InvariantViolation(
                "RiskBreach current value must exceed or equal limit"
            )
