from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.money import Money


@dataclass(frozen=True)
class DrawdownLimit(ValueObject):
    value: Money

    def _validate(self) -> None:
        if self.value.value <= Decimal("0"):
            raise InvariantViolation("Max drawdown must be strictly positive")
