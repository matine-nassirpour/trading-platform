from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.algebraic_monetary_value_object import (
    AlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True)
class Equity(AlgebraicMonetaryValueObject):
    """
    Trading equity.
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        # Equity can be negative (margin trading)
        pass

    def add(self, other: MonetaryAmount) -> Equity:
        if not isinstance(other, RealizedPnL):
            raise InvariantViolation("Equity can only be adjusted by RealizedPnL")

        self._check_currency(other)

        return Equity(
            value=self.value + other.value,
            currency=self.currency,
        )

    def subtract(self, other: MonetaryAmount) -> Equity:
        if not isinstance(other, RealizedPnL):
            raise InvariantViolation("Equity can only be adjusted by RealizedPnL")

        self._check_currency(other)

        return Equity(
            value=self.value - other.value,
            currency=self.currency,
        )
