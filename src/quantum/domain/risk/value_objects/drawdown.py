from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Drawdown(ContextualMonetaryAmount):
    """
    Drawdown = equity_peak − equity.

    Properties:
    - Always ≥ 0
    - Bound to a MoneyContext
    - Non-algebraic (cannot be added/subtracted)
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("Drawdown must be non-negative")
