from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class TickValue(ValueObject):
    """
    Monetary value of one tick movement for one contract.
    """

    value: Decimal
    currency: Currency

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("TickValue must be a Decimal")

        if self.value <= Decimal("0"):
            raise InvariantViolation("TickValue must be strictly positive")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("TickValue must have a valid Currency")
