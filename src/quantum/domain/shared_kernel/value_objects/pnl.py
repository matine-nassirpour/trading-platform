from dataclasses import dataclass

from quantum.domain.shared_kernel.money.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class RealizedPnL(SignedContextualAmount):
    """
    Realized profit and loss from executed trades.
    """

    pass


@dataclass(frozen=True, slots=True)
class UnrealizedPnL(SignedContextualAmount):
    """
    Unrealized profit and loss bound to a MoneyContext.
    """

    pass
