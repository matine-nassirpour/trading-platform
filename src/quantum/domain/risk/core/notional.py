from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Notional(ContextualMonetaryAmount):
    """
    Gross notional exposure.

    Properties:
    - Always non-negative
    - Currency-aware
    - NOT algebraically composable
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("Notional must be non-negative")
