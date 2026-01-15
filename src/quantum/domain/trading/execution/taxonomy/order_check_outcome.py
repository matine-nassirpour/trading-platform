from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderCheckOutcome(ClosedSetValueObject):
    """
    Outcome of pre-execution order checks.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "accepted",
            "insufficient_margin",
            "invalid_price",
            "invalid_volume",
            "market_closed",
            "unknown_error",
        }
    )
