from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class Fee(ValueObject):
    """
    Canonical execution fee.
    Always non-negative.
    """

    value: Decimal
    currency: Currency

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Fee value must be a Decimal")

        if self.value < Decimal("0"):
            raise InvariantViolation("Fee must be non-negative")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("Fee must have a valid Currency")
