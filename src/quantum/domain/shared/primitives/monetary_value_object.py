from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import CurrencyMismatch, InvariantViolation
from quantum.domain.shared.primitives.numeric_value_object import NumericValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class MonetaryValueObject(NumericValueObject, ABC):
    """
    Canonical base class for all monetary value objects.

    Design guarantees:
    - Decimal-based arithmetic only
    - Explicit Currency
    - No NaN / Infinity
    - Deterministic and auditable semantics
    - Safe monetary comparisons and operations
    """

    value: Decimal
    currency: Currency

    # --- Validation ----------------------------------------------------------

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal"
            )

        if not isinstance(self.currency, Currency):
            raise InvariantViolation(
                f"{self.__class__.__name__} must have a valid Currency"
            )

    # NOTE:
    # _validate_semantics() remains abstract
    # and must be implemented by concrete subclasses
    # (e.g. >= 0, > 0, bounded, etc.)

    # --- Shared monetary helpers ---------------------------------------------

    def _check_currency(self, other: MonetaryValueObject) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    # --- Safe arithmetic -----------------------------------------------------

    def __add__(self, other: MonetaryValueObject) -> MonetaryValueObject:
        self._check_currency(other)
        return self.__class__(
            value=self.value + other.value,
            currency=self.currency,
        )

    def __sub__(self, other: MonetaryValueObject) -> MonetaryValueObject:
        self._check_currency(other)
        return self.__class__(
            value=self.value - other.value,
            currency=self.currency,
        )

    # --- Comparisons (currency-safe) -----------------------------------------

    def __lt__(self, other: MonetaryValueObject) -> bool:
        self._check_currency(other)
        return self.value < other.value

    def __le__(self, other: MonetaryValueObject) -> bool:
        self._check_currency(other)
        return self.value <= other.value

    def __gt__(self, other: MonetaryValueObject) -> bool:
        self._check_currency(other)
        return self.value > other.value

    def __ge__(self, other: MonetaryValueObject) -> bool:
        self._check_currency(other)
        return self.value >= other.value
