from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class PositionSide(ClosedSetValueObject):
    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset({"long", "short"})

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

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
