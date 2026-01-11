from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.contextual_algebraic_monetary_value_object import (
    ContextualAlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class UnrealizedPnL(ContextualAlgebraicMonetaryValueObject):
    """
    Unrealized PnL bound to a MoneyContext.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
        # No restriction: UnrealizedPnL ∈ ℝ
        pass

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._check_currency_and_context(other)
        return UnrealizedPnL(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: UnrealizedPnL) -> UnrealizedPnL:
        self._check_currency_and_context(other)
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
