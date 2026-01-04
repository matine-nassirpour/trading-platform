from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class DrawdownLimit(ValueObject):
    """
    Maximum allowed drawdown.
    """

    value: MonetaryValueObject

    def _validate(self) -> None:
        if self.value.value <= Decimal("0"):
            raise InvariantViolation("Max drawdown must be strictly positive")
