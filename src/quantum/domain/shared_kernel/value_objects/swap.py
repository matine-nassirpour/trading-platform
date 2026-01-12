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
class Swap(ContextualAlgebraicMonetaryValueObject):
    """
    Swap / rollover monetary adjustment.

    Properties:
    - Can be positive or negative
    - Currency-aware
    - Context-aware
    - Algebraically composable only with compatible Swap
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
        """
        Swap ∈ ℝ (no restriction on sign).

        Inherits:
        - Decimal-only
        - Finite
        - Currency consistency
        - MoneyContext consistency
        """
        super()._validate_semantics()

    # --- Algebraic operations -------------------------------------------------

    def add(self, other: Swap) -> Swap:
        """
        Returns a new Swap equal to this ⊕ other.
        """
        self._assert_algebraically_compatible(other)
        return Swap(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: Swap) -> Swap:
        """
        Returns a new Swap equal to this ⊖ other.
        """
        self._assert_algebraically_compatible(other)
        return Swap(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )

    @staticmethod
    def zero(context: MoneyContext) -> Swap:
        """
        Canonical zero Swap for a given MoneyContext.
        """
        return Swap(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )
