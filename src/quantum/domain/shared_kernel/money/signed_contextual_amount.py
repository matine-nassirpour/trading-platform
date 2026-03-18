from __future__ import annotations

from abc import ABC
from decimal import Decimal
from typing import TypeVar, final

from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext

T = TypeVar("T", bound="SignedContextualAmount")


class SignedContextualAmount(ContextualMonetaryAmount, ABC):
    """
    Algebraic base class for signed monetary domain quantities.

    HARD GUARANTEES:
    - Closed operations preserve concrete nominal type
    - Cross-type arithmetic is forbidden at runtime
    - Cross-context arithmetic is forbidden
    - Cross-currency arithmetic is forbidden

    DOMAIN CONSEQUENCE:
    RealizedPnL and UnrealizedPnL are intentionally NOT interchangeable,
    even though they share the same physical representation.
    """

    __slots__ = ()

    # --- Closed algebra -------------------------------------------------------

    @final
    def add(self: T, other: T) -> T:
        self._assert_closed_algebra_compatibility(other)
        return self._new(self.value + other.value)

    @final
    def subtract(self: T, other: T) -> T:
        self._assert_closed_algebra_compatibility(other)
        return self._new(self.value - other.value)

    @final
    def negate(self: T) -> T:
        return self._new(-self.value)

    @final
    def absolute(self: T) -> T:
        return self._new(abs(self.value))

    # --- Factory --------------------------------------------------------------

    @classmethod
    @final
    def zero(cls: type[T], context: MoneyContext) -> T:
        return cls(
            value=Decimal("0"),
            currency=context.reporting_currency,
            context=context,
        )

    # --- Internal constructor -------------------------------------------------

    @final
    def _new(self: T, value: Decimal) -> T:
        """
        Returns a new instance of the SAME concrete nominal type.

        This is the single canonical reconstruction path for algebraic operations.
        """
        rebuilt = self._rebuild_with_value(value)

        if type(rebuilt) is not type(self):
            raise TypeError(
                f"{self.__class__.__name__} reconstruction violated nominal closure: "
                f"expected {type(self).__name__}, got {type(rebuilt).__name__}."
            )

        return rebuilt
