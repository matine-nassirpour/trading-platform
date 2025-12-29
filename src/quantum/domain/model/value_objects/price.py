from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class Price(ValueObject):
    value: Decimal

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Price value must be a Decimal")

        if self.value <= Decimal("0"):
            raise InvariantViolation("Price must be strictly positive")
