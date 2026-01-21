from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Balance(ContextualMonetaryAmount):
    """
    Represents a monetary balance (cash, equity, margin).
    """

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Balance must be a Decimal")

    def add(self, other: Balance) -> Balance:
        self._assert_same_context_and_currency(other)
        return Balance(
            value=self.value + other.value,
            currency=self.currency,
            context=self.context,
        )

    def subtract(self, other: Balance) -> Balance:
        self._assert_same_context_and_currency(other)
        return Balance(
            value=self.value - other.value,
            currency=self.currency,
            context=self.context,
        )
