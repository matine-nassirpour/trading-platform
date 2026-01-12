from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
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

    def _assert_algebraically_compatible(self, other: Self) -> None:
        """
        Enforces algebraic closure:
        - same monetary frame
        - same runtime type
        """

        if type(self) is not type(other):
            raise InvariantViolation(
                f"Algebraic type mismatch: {type(self).__name__} vs {type(other).__name__}"
            )

        # Delegate currency & context to the canonical checker
        self._assert_same_context_and_currency(other)

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
