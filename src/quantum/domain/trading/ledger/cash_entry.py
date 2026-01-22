from dataclasses import dataclass

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
