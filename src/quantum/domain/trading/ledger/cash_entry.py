from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class CashEntry(ContextualMonetaryAmount):
    """
    Represents a movement of cash in the ledger.

    Examples:
    - deposit
    - withdrawal
    - realized PnL
    - fee deduction
    """

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.value, Decimal):
            raise InvariantViolation("CashEntry value must be Decimal")
