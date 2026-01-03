from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.numeric_value_object import _NumericValueObject


@dataclass(frozen=True)
class Price(_NumericValueObject):
    value: Decimal

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Price value must be a Decimal")

        if self.value <= Decimal("0"):
            raise InvariantViolation("Price must be strictly positive")
