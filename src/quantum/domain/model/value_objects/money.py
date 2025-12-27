from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext

from quantum.domain.model.exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject

getcontext().prec = 28  # deterministic financial precision


@dataclass(frozen=True)
class Money(ValueObject):
    value: Decimal
    currency: str = "USD"

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Money value must be Decimal")

        if self.currency is None or not self.currency.isalpha():
            raise InvariantViolation("Invalid currency code")

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.value + other.value, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.value - other.value, self.currency)

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise InvariantViolation("Currency mismatch")
