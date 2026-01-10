from __future__ import annotations

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount


class ContextualAlgebraicMonetaryValueObject(
    ContextualMonetaryAmount,
    ABC,
):
    """
    Algebraic monetary value bound to a MoneyContext.

    Guarantees:
    - Currency consistency
    - Context consistency
    - Safe algebraic operations
    """

    def _check_currency_and_context(
        self, other: ContextualAlgebraicMonetaryValueObject
    ) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context} vs {other.context}"
            )

    @abstractmethod
    def add(self, other: MonetaryAmount) -> MonetaryAmount:
        raise NotImplementedError

    @abstractmethod
    def subtract(self, other: MonetaryAmount) -> MonetaryAmount:
        raise NotImplementedError
