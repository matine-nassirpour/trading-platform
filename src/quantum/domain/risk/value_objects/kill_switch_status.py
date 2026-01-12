from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class KillSwitchStatus(ClosedSetValueObject):
    """
    Canonical kill switch status.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "armed",
            "triggered",
        }
    )

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    @classmethod
    def armed(cls) -> KillSwitchStatus:
        return cls("armed")

    @classmethod
    def triggered(cls) -> KillSwitchStatus:
        return cls("triggered")
