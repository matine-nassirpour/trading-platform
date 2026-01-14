from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class RealizedPnL(ContextualMonetaryAmount):
    """
    Realized profit and loss from executed trades.

    PnL is a contextual monetary flux.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _validate(self) -> None:
        # All base monetary & contextual invariants
        super()._validate()
        # No restriction on sign (can be positive or negative)

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: RealizedPnL) -> RealizedPnL:
        self._assert_same_context_and_currency(other)
        return RealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: RealizedPnL) -> RealizedPnL:
        self._assert_same_context_and_currency(other)
        return RealizedPnL(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )

    @staticmethod
    def zero(context: MoneyContext) -> RealizedPnL:
        return RealizedPnL(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )
