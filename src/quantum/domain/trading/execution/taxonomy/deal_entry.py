from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DealEntry(ClosedSetValueObject):
    """
    Deal entry direction.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "in",
            "out",
        }
    )

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
