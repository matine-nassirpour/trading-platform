from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
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
    def armed(cls) -> KillSwitchStatus:
        return cls("armed")

    @classmethod
    def triggered(cls) -> KillSwitchStatus:
        return cls("triggered")
