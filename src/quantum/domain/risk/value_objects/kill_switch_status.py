from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class KillSwitchStatus(ClosedSetValueObject):
    """
    Canonical kill switch status.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "armed",
                "triggered",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def armed(cls) -> KillSwitchStatus:
        return cls("armed")

    @classmethod
    def triggered(cls) -> KillSwitchStatus:
        return cls("triggered")
