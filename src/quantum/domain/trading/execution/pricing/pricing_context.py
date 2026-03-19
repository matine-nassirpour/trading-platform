from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class PricingContext(ClosedSetValueObject):
    """
    Canonical pricing context.

    Defines WHY a price is quantized, not HOW.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "neutral",
                "execution_sl",
                "execution_tp",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def neutral(cls) -> PricingContext:
        return cls("neutral")

    @classmethod
    def execution_sl(cls) -> PricingContext:
        return cls("execution_sl")

    @classmethod
    def execution_tp(cls) -> PricingContext:
        return cls("execution_tp")

    # --- Semantic helpers -----------------------------------------------------

    def is_neutral(self) -> bool:
        return self.value == "neutral"

    def is_execution_sl(self) -> bool:
        return self.value == "execution_sl"

    def is_execution_tp(self) -> bool:
        return self.value == "execution_tp"
