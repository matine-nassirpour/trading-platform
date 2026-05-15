from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.monetary.signed_contextual_amount import (
    SignedContextualAmount,
)


@dataclass(frozen=True, slots=True)
class Swap(SignedContextualAmount):
    """
    Swap / rollover monetary adjustment.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "swap"
