from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.contextual_algebraic_monetary_value_object import (
    ContextualAlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class RealizedPnL(ContextualAlgebraicMonetaryValueObject):
    """
    Realized profit and loss from executed trades.

    PnL is a contextual monetary flux.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _validate_semantics(self) -> None:
        # No restriction: PnL ∈ ℝ
        pass

    # --- Algebraic operations (explicit, safe) --------------------------------

    def add(self, other: RealizedPnL) -> RealizedPnL:
        self._check_currency(other)
        self._check_context(other)
        return RealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: RealizedPnL) -> RealizedPnL:
        self._check_currency(other)
        self._check_context(other)
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
