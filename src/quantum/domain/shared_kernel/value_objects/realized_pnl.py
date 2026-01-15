from dataclasses import dataclass

from quantum.domain.shared_kernel.money.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class RealizedPnL(SignedContextualAmount):
    """
    Realized profit and loss from executed trades.

    PnL is a contextual monetary flux.
    """

    # No extra invariants
    pass
