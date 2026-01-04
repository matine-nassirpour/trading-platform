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
class UnrealizedPnL(AlgebraicMonetaryValueObject):
    """
    Unrealized Profit and Loss.

    Properties:
    - Derived, non-settled monetary variation
    - Can be positive, zero, or negative
    - Algebraically composable
    """

    value: Decimal
    currency: Currency

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
        # No restriction: UnrealizedPnL ∈ ℝ
        pass

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: MonetaryAmount) -> UnrealizedPnL:
        if not isinstance(other, UnrealizedPnL):
            raise InvariantViolation("UnrealizedPnL can only be added to UnrealizedPnL")

        self._check_currency(other)

        return UnrealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
        )

    def subtract(self, other: MonetaryAmount) -> UnrealizedPnL:
        if not isinstance(other, UnrealizedPnL):
            raise InvariantViolation(
                "UnrealizedPnL can only be subtracted from UnrealizedPnL"
            )

        self._check_currency(other)

        return UnrealizedPnL(
            value=self.value - other.value,
            currency=self.currency,
        )

    @staticmethod
    def zero(currency: Currency) -> UnrealizedPnL:
        """
        Canonical zero unrealized PnL.
        """
        return UnrealizedPnL(
            value=Decimal("0"),
            currency=currency,
        )
