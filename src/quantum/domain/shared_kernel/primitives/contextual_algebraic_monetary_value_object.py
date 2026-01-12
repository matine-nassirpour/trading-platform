from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


class ContextualAlgebraicMonetaryValueObject(ContextualMonetaryAmount, ABC):
    """
    Algebraic monetary value bound to a MoneyContext.

    Algebraic contract:
    - Closed under + and −
    - Currency invariant
    - Context invariant
    """

    # --- Algebraic invariants -------------------------------------------------

    def _check_currency_and_context(self, other: ContextualMonetaryAmount) -> None:
        if not isinstance(other, ContextualAlgebraicMonetaryValueObject):
            raise InvariantViolation(
                "Operand must be a ContextualAlgebraicMonetaryValueObject"
            )

        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

        if self.context != other.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {self.context} vs {other.context}"
            )

    # --- Algebraic operations -------------------------------------------------

    @abstractmethod
    def add(self, other: Self) -> Self:
        """
        Returns self ⊕ other.

        Must preserve:
        - type
        - currency
        - MoneyContext
        """
        raise NotImplementedError

    @abstractmethod
    def subtract(self, other: Self) -> Self:
        """
        Returns self ⊖ other.

        Must preserve:
        - type
        - currency
        - MoneyContext
        """
        raise NotImplementedError
