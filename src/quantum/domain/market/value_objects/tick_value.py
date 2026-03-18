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

    @classmethod
    def nominal_type(cls) -> str:
        return "tick_value"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("TickValue must be strictly positive")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("TickValue requires a valid Currency")
