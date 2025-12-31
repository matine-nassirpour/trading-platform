from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class PositionSide(ClosedSetValueObject):
    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset({"long", "short"})

    @classmethod
    def long(cls) -> PositionSide:
        return cls("long")

    @classmethod
    def short(cls) -> PositionSide:
        return cls("short")

    # --- Semantic helpers -----------------------------------------------------

    def is_long(self) -> bool:
        return self.value == "long"

    def is_short(self) -> bool:
        return self.value == "short"

    def sign(self) -> int:
        return 1 if self.is_long() else -1
