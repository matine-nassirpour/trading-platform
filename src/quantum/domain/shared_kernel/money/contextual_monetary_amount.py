from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.money.money_context import MoneyContext


@dataclass(frozen=True, slots=True)
class ContextualMonetaryAmount(MonetaryAmount):
    """
    Monetary amount bound to a specific MoneyContext.

    Prevents cross-currency and cross-context contamination.
    """

    context: MoneyContext

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a MoneyContext"
            )

        if self.currency not in self.context.allowed_currencies:
            raise InvariantViolation(
                f"Currency {self.currency} not allowed in MoneyContext {self.context}"
            )

    # --- Canonical algebraic invariant ----------------------------------------

    def _assert_same_context_and_currency(
        self, other: ContextualMonetaryAmount
    ) -> None:
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
