from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.algebraic_monetary_value_object import (
    AlgebraicMonetaryValueObject,
)
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class RealizedPnL(AlgebraicMonetaryValueObject):
    """
    Realized profit and loss from executed trades.
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        # No restriction: PnL ∈ ℝ
        pass

    # --- Algebraic operations (explicit, safe) --------------------------------

    def add(self, other: MonetaryAmount) -> RealizedPnL:
        if not isinstance(other, RealizedPnL):
            raise InvariantViolation("RealizedPnL can only be added to RealizedPnL")

        self._check_currency(other)
        return RealizedPnL(self.value + other.value, self.currency)

    def subtract(self, other: MonetaryAmount) -> RealizedPnL:
        if not isinstance(other, RealizedPnL):
            raise InvariantViolation(
                "RealizedPnL can only be subtracted from RealizedPnL"
            )

        self._check_currency(other)
        return RealizedPnL(self.value - other.value, self.currency)

    @staticmethod
    def zero(currency: Currency) -> RealizedPnL:
        return RealizedPnL(
            value=Decimal("0"),
            currency=currency,
        )
