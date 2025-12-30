from dataclasses import dataclass
from typing import Literal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.money import Money


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
