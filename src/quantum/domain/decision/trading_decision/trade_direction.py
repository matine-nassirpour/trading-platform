from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class TradeDirection(ClosedSetValueObject):
    """
    Direction asserted by the decision domain.

    This represents the directional stance of a trade candidate,
    not the side of an actually held position.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset({"long", "short"})

    @classmethod
    def long(cls) -> TradeDirection:
        return cls("long")

    @classmethod
    def short(cls) -> TradeDirection:
        return cls("short")

    def is_long(self) -> bool:
        return self.value == "long"

    def is_short(self) -> bool:
        return self.value == "short"

    def sign(self) -> int:
        return 1 if self.is_long() else -1
