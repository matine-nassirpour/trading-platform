from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.numeric_value_object import _NumericValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class Drawdown(_NumericValueObject):
    """
    Positive drawdown value expressed in monetary units.

    Invariants:
    - value >= 0
    - finite Decimal
    - explicit Currency
    """

    value: Decimal
    currency: Currency

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Drawdown value must be a Decimal")

        if self.value < Decimal("0"):
            raise InvariantViolation("Drawdown must be non-negative")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("Drawdown must have a valid Currency")
