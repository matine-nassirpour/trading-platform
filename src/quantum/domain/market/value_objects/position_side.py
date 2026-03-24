from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class PositionSide(ClosedSetValueObject):
    """
    Long / Short position side.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset({"long", "short"})

    # --- Named constructors ---------------------------------------------------

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
