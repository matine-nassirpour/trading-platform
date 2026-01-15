from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class LatencyPhase(ClosedSetValueObject):
    """
    Execution latency measurement phase.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "terminal_ping",
            "order_check",
            "order_send",
            "ack",
            "fill",
        }
    )
