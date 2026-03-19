from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationStatus(ClosedSetValueObject):
    """
    Canonical authorization status.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "authorized",
                "rejected",
            }
        )

    @classmethod
    def authorized(cls) -> DecisionAuthorizationStatus:
        return cls("authorized")

    @classmethod
    def rejected(cls) -> DecisionAuthorizationStatus:
        return cls("rejected")

    def is_authorized(self) -> bool:
        return self.value == "authorized"

    def is_rejected(self) -> bool:
        return self.value == "rejected"
