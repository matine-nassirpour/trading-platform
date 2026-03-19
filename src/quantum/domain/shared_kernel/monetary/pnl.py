from dataclasses import dataclass

from quantum.domain.shared_kernel.monetary.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class RealizedPnL(SignedContextualAmount):
    """
    Realized profit and loss from executed trades.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "realized_pnl"


@dataclass(frozen=True, slots=True)
class UnrealizedPnL(SignedContextualAmount):
    """
    Unrealized profit and loss bound to a MoneyContext.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "unrealized_pnl"
