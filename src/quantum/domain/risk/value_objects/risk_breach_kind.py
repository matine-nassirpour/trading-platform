from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
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
