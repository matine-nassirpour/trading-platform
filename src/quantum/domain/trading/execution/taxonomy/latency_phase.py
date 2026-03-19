from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class LatencyPhase(ClosedSetValueObject):
    """
    Execution latency measurement phase.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "terminal_ping",
                "order_check",
                "order_send",
                "ack",
                "fill",
            }
        )
