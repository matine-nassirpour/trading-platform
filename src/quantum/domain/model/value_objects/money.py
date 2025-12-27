from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.policies.monetary_policy import MonetaryPolicy


@dataclass(frozen=True)
class Money(ValueObject):
    value: Decimal
    currency: str = "USD"

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Money value must be a Decimal")

        if not self.currency or not self.currency.isalpha() or len(self.currency) != 3:
            raise InvariantViolation("Currency must be a 3-letter ISO code")

        quantized = MonetaryPolicy.quantize_money(self.value)

        object.__setattr__(self, "value", quantized)
        object.__setattr__(self, "currency", self.currency.upper())

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
