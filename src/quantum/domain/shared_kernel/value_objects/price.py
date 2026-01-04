from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True)
class Price(NumericValueObject):
    """
    Strictly positive monetary quantity.
    """

    value: Decimal

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Price value must be a Decimal")

    def _validate_semantics(self) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("Price must be strictly positive")
