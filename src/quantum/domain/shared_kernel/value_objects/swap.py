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
class Swap(AlgebraicMonetaryValueObject):
    """
    Swap / rollover monetary adjustment.

    Properties:
    - Can be positive or negative
    - Currency-aware
    - Algebraically composable (Swap ⊕ Swap)
    """

    value: Decimal
    currency: Currency

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
        # Swap ∈ ℝ (no restriction)
        pass

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: MonetaryAmount) -> Swap:
        if not isinstance(other, Swap):
            raise InvariantViolation("Swap can only be added to Swap")

        self._check_currency(other)

        return Swap(
            value=self.value + other.value,
            currency=self.currency,
        )

    def subtract(self, other: MonetaryAmount) -> Swap:
        if not isinstance(other, Swap):
            raise InvariantViolation("Swap can only be subtracted from Swap")

        self._check_currency(other)

        return Swap(
            value=self.value - other.value,
            currency=self.currency,
        )

    @staticmethod
    def zero(currency: Currency) -> Swap:
        """
        Canonical zero swap.
        """
        return Swap(
            value=Decimal("0"),
            currency=currency,
        )
