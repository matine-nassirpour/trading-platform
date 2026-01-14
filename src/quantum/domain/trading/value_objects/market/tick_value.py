from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class TickValue(NumericValueObject):
    """
    Monetary value of one tick movement for one contract.
    """

    currency: Currency

    def _validate(self) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("TickValue must be strictly positive")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("TickValue requires a valid Currency")
