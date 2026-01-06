from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.algebraic_monetary_value_object import (
    AlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class Fee(AlgebraicMonetaryValueObject):
    """
    Canonical execution fee.

    Properties:
    - Always non-negative
    - Currency-aware
    - Algebraically composable
    """

    value: Decimal
    currency: Currency

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("Fee must be non-negative")

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: MonetaryAmount) -> Fee:
        if not isinstance(other, Fee):
            raise InvariantViolation("Fee can only be added to Fee")

        self._check_currency(other)

        return Fee(
            value=self.value + other.value,
            currency=self.currency,
        )

    def subtract(self, other: MonetaryAmount) -> Fee:
        if not isinstance(other, Fee):
            raise InvariantViolation("Fee can only be subtracted from Fee")

        self._check_currency(other)

        result = self.value - other.value

        if result < Decimal("0"):
            raise InvariantViolation("Fee subtraction cannot produce a negative value")

        return Fee(
            value=result,
            currency=self.currency,
        )
