from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class RiskBreachKind(ClosedSetValueObject):
    """
    Canonical risk breach category.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "drawdown",
            "notional",
            "daily_loss",
        }
    )

    @classmethod
    def drawdown(cls) -> RiskBreachKind:
        return cls("drawdown")

    @classmethod
    def notional(cls) -> RiskBreachKind:
        return cls("notional")

    @classmethod
    def daily_loss(cls) -> RiskBreachKind:
        return cls("daily_loss")
