from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderCheckOutcome(ClosedSetValueObject):
    """
    Outcome of pre-execution order checks.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "accepted",
                "insufficient_margin",
                "invalid_price",
                "invalid_volume",
                "market_closed",
                "unknown_error",
            }
        )
