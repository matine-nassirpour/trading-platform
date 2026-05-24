from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderFillStatus(ClosedSetValueObject):
    """
    Economic fill status.

    This represents HOW MUCH of the order has been filled.
    It does NOT represent broker lifecycle state.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "unfilled",
                "partially_filled",
                "filled",
            }
        )

    @classmethod
    def unfilled(cls) -> OrderFillStatus:
        return cls("unfilled")

    @classmethod
    def partially_filled(cls) -> OrderFillStatus:
        return cls("partially_filled")

    @classmethod
    def filled(cls) -> OrderFillStatus:
        return cls("filled")

    def is_unfilled(self) -> bool:
        return self.value == "unfilled"

    def is_partially_filled(self) -> bool:
        return self.value == "partially_filled"

    def is_filled(self) -> bool:
        return self.value == "filled"
