from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext


@dataclass(frozen=True, slots=True)
class UnrealizedPnL(ContextualMonetaryAmount):
    """
    Unrealized profit and loss bound to a MoneyContext.
    """

    def _validate(self) -> None:
        super()._validate()
        # No restriction on sign

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._assert_same_context_and_currency(other)
        return UnrealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._assert_same_context_and_currency(other)
        return UnrealizedPnL(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )

    @staticmethod
    def zero(context: MoneyContext) -> UnrealizedPnL:
        return UnrealizedPnL(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )
