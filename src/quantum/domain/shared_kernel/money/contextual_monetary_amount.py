from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class ContextualMonetaryAmount(MonetaryAmount, ABC):
    """
    Monetary amount bound to a specific MoneyContext.

    This prevents cross-currency contamination at the system level.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _validate_semantics(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("ContextualMonetaryAmount requires a MoneyContext")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("ContextualMonetaryAmount requires a Currency")

        if self.currency != self.context.reporting_currency:
            raise InvariantViolation(
                f"Currency {self.currency} does not match MoneyContext {self.context.reporting_currency}"
            )

    def _check_currency_and_context(self, other: ContextualMonetaryAmount) -> None:
        if not isinstance(other, ContextualMonetaryAmount):
            raise InvariantViolation("Operand must be a ContextualMonetaryAmount")

        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context} vs {other.context}"
            )
