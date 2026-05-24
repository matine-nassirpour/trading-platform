from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderLifecycleStatus(ClosedSetValueObject):
    """
    Operational OMS lifecycle status.

    This represents WHERE the order is in the broker / execution lifecycle.
    It does NOT represent economic fill state.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "created",
                "submitted",
                "acknowledged",
                "accepted",
                "rejected",
                "cancelled",
                "expired",
            }
        )

    @classmethod
    def created(cls) -> OrderLifecycleStatus:
        return cls("created")

    @classmethod
    def submitted(cls) -> OrderLifecycleStatus:
        return cls("submitted")

    @classmethod
    def acknowledged(cls) -> OrderLifecycleStatus:
        return cls("acknowledged")

    @classmethod
    def accepted(cls) -> OrderLifecycleStatus:
        return cls("accepted")

    @classmethod
    def rejected(cls) -> OrderLifecycleStatus:
        return cls("rejected")

    @classmethod
    def cancelled(cls) -> OrderLifecycleStatus:
        return cls("cancelled")

    @classmethod
    def expired(cls) -> OrderLifecycleStatus:
        return cls("expired")

    def is_terminal(self) -> bool:
        return self.value in {
            "rejected",
            "cancelled",
            "expired",
        }

    def can_receive_fill(self) -> bool:
        return self.value in {
            "accepted",
            "acknowledged",
        }

    def can_be_cancelled(self) -> bool:
        return self.value in {
            "created",
            "submitted",
            "acknowledged",
            "accepted",
        }
