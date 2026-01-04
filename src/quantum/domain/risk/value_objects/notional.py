from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class Notional(MonetaryValueObject):
    """
    Gross notional exposure.

    Properties:
    - Always non-negative
    - Currency-aware
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("Notional must be non-negative")
