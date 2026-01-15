from __future__ import annotations

from abc import ABC
from decimal import Decimal
from typing import TypeVar

from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext

T = TypeVar("T", bound="SignedContextualAmount")


class SignedContextualAmount(ContextualMonetaryAmount, ABC):
    """
    Algebraic base class for all signed monetary fluxes.

    This class provides:
    - add
    - subtract
    - zero()

    without duplicating logic across semantic subtypes.

    Subclasses remain nominally distinct
    (RealizedPnL != UnrealizedPnL != Swap).
    """

    # --- Algebraic operations -------------------------------------------------

    def add(self: T, other: T) -> T:
        self._assert_same_context_and_currency(other)
        return self._new(self.value + other.value)

    def subtract(self: T, other: T) -> T:
        self._assert_same_context_and_currency(other)
        return self._new(self.value - other.value)

    # --- Factory --------------------------------------------------------------

    @classmethod
    def zero(cls: type[T], context: MoneyContext) -> T:
        return cls(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )

    # --- Internal constructor -------------------------------------------------

    def _new(self: T, value: Decimal) -> T:
        """
        Constructs a new instance of the SAME concrete type
        with the given value.

        This preserves nominal typing and invariants.
        """
        return self.__class__(
            value=value,
            currency=self.currency,
            context=self.context,
        )
