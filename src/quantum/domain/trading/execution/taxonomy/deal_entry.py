from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


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

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

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
