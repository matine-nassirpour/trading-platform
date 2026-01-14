from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext


@dataclass(frozen=True, slots=True)
class Swap(ContextualMonetaryAmount):
    """
    Swap / rollover monetary adjustment.

    Properties:
    - Can be positive or negative
    - Currency-aware
    - Context-aware
    """

    def _validate(self) -> None:
        super()._validate()
        # No restriction on sign

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: Swap) -> Swap:
        self._assert_same_context_and_currency(other)
        return Swap(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: Swap) -> Swap:
        self._assert_same_context_and_currency(other)
        return Swap(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )

    @staticmethod
    def zero(context: MoneyContext) -> Swap:
        return Swap(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )
