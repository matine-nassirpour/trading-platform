from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.money import Money


@dataclass(frozen=True)
class DrawdownLimit(ValueObject):
    value: Money

    def _validate(self) -> None:
        if self.value.value <= Decimal("0"):
            raise InvariantViolation("Max drawdown must be strictly positive")
