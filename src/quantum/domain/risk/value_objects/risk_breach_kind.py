from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class RiskBreachKind(ClosedSetValueObject):
    """
    Canonical risk breach category.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "drawdown",
                "notional",
                "daily_loss",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def drawdown(cls) -> RiskBreachKind:
        return cls("drawdown")

    @classmethod
    def notional(cls) -> RiskBreachKind:
        return cls("notional")

    @classmethod
    def daily_loss(cls) -> RiskBreachKind:
        return cls("daily_loss")
