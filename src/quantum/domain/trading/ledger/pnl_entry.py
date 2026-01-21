from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class PnLEntry(ContextualMonetaryAmount):
    """
    Represents realized or unrealized PnL.

    Positive → profit
    Negative → loss
    """

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.value, Decimal):
            raise InvariantViolation("PnLEntry must be a Decimal")
