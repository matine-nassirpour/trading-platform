from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import CurrencyMismatch, InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class Money(ValueObject):
    """
    Monetary Value Object.

    Guarantees:
    - Decimal-based arithmetic
    - Currency safety
    - No NaN / Infinity
    """

    value: Decimal
    currency: Currency

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Money value must be a Decimal")

        if self.value.is_nan():
            raise InvariantViolation("Money value must not be NaN")

        if self.value.is_infinite():
            raise InvariantViolation("Money value must be finite")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("Money must have a valid Currency")

    # --- Factories ------------------------------------------------------------

    @staticmethod
    def zero(currency: Currency) -> Money:
        """
        Canonical zero monetary value.
        """
        return Money(Decimal("0"), currency)

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
