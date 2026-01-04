from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class Drawdown(MonetaryAmount):
    """
    Positive drawdown expressed in monetary units.

    NOTE:
    - NOT algebraically composable
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("Drawdown must be non-negative")
