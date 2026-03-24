from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
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

    @classmethod
    def nominal_type(cls) -> str:
        return "daily_loss"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value < Decimal("0"):
            raise InvariantViolation("DailyLoss must be non-negative")
