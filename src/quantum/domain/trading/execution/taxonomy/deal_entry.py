from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DealEntry(ClosedSetValueObject):
    """
    Deal entry direction.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "in",
                "out",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def in_(cls) -> DealEntry:
        return cls("in")

    @classmethod
    def out(cls) -> DealEntry:
        return cls("out")

    # --- Semantic helpers -----------------------------------------------------

    def is_in(self) -> bool:
        return self.value == "in"

    def is_out(self) -> bool:
        return self.value == "out"
