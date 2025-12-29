from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.currency import Currency


@dataclass(frozen=True)
class Money(ValueObject):
    value: Decimal
    currency: Currency

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Money value must be a Decimal")

    # --- Internal helpers -----------------------------------------------------

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    # --- Arithmetic -----------------------------------------------------------

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.value + other.value, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.value - other.value, self.currency)
