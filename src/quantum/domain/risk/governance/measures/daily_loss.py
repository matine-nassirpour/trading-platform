from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class DailyLoss(ContextualMonetaryAmount):
    """
    Accumulated realized loss for the current trading day.

    Properties:
    - Always ≥ 0
    - Bound to a MoneyContext
    - Non-algebraic
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("DailyLoss must be non-negative")
