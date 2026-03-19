from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class LiquiditySide(ClosedSetValueObject):
    """
    Liquidity side of an execution.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "maker",
                "taker",
                "unknown",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def maker(cls) -> LiquiditySide:
        return cls("maker")

    @classmethod
    def taker(cls) -> LiquiditySide:
        return cls("taker")

    @classmethod
    def unknown(cls) -> LiquiditySide:
        return cls("unknown")
