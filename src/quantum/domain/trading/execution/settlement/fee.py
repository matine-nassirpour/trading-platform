from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Fee(ContextualMonetaryAmount):
    """
    Canonical execution fee.

    Properties:
    - Always non-negative
    - Currency-aware
    - Algebraically composable
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("Fee must be non-negative")

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: Fee) -> Fee:
        self._assert_same_context_and_currency(other)
        return Fee(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: Fee) -> Fee:
        self._assert_same_context_and_currency(other)

        result = self.value - other.value

        if result < Decimal("0"):
            raise InvariantViolation("Fee subtraction cannot produce a negative value")

        return Fee(
            value=result,
            currency=self.currency,
            context=self.context,
        )
