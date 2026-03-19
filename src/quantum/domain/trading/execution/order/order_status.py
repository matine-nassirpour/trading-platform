from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderStatus(ClosedSetValueObject):

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "pending",
                "partially_filled",
                "filled",
                "rejected",
                "cancelled",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def pending(cls) -> OrderStatus:
        return cls("pending")

    @classmethod
    def partially_filled(cls) -> OrderStatus:
        return cls("partially_filled")

    @classmethod
    def filled(cls) -> OrderStatus:
        return cls("filled")

    @classmethod
    def cancelled(cls) -> OrderStatus:
        return cls("cancelled")

    @classmethod
    def rejected(cls) -> OrderStatus:
        return cls("rejected")

    # --- Semantic helpers -----------------------------------------------------

    def is_pending(self) -> bool:
        return self.value == "pending"

    def is_partially_filled(self) -> bool:
        return self.value == "partially_filled"

    def is_filled(self) -> bool:
        return self.value == "filled"

    def is_cancelled(self) -> bool:
        return self.value == "cancelled"

    def is_rejected(self) -> bool:
        return self.value == "rejected"

    def is_terminal(self) -> bool:
        return self.value in {
            "filled",
            "cancelled",
            "rejected",
        }

    def is_fillable(self) -> bool:
        return self.value in {
            "pending",
            "partially_filled",
        }
