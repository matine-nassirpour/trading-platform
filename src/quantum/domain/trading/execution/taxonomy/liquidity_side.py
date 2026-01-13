from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class LiquiditySide(ClosedSetValueObject):
    """
    Liquidity side of an execution.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "maker",
            "taker",
            "unknown",
        }
    )

    def _closed_set_type(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    @classmethod
    def maker(cls) -> LiquiditySide:
        return cls("maker")

    @classmethod
    def taker(cls) -> LiquiditySide:
        return cls("taker")

    @classmethod
    def unknown(cls) -> LiquiditySide:
        return cls("unknown")
