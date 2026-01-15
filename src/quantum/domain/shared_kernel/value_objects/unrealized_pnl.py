from dataclasses import dataclass

from quantum.domain.shared_kernel.money.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class UnrealizedPnL(SignedContextualAmount):
    """
    Unrealized profit and loss bound to a MoneyContext.
    """

    # No extra invariants
    pass
