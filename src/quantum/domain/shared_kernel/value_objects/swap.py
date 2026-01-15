from dataclasses import dataclass

from quantum.domain.shared_kernel.money.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class Swap(SignedContextualAmount):
    """
    Swap / rollover monetary adjustment.
    """

    # No extra invariants
    pass
