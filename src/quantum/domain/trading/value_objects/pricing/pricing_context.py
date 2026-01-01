from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class PricingContext(ClosedSetValueObject):
    """
    Canonical pricing context.

    Defines WHY a price is quantized, not HOW.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "neutral",
            "execution_sl",
            "execution_tp",
        }
    )

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
