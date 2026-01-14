from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class DailyLossLimit(ContextualMonetaryAmount):
    """
    Maximum allowed realized loss per trading day.

    Properties:
    - Strictly positive
    - Contextual
    - Non-algebraic
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value <= Decimal("0"):
            raise InvariantViolation("DailyLossLimit must be strictly positive")
