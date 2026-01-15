from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DealReason(ClosedSetValueObject):
    """
    Reason for deal execution.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "client",  # user / algo
                "mobile",
                "web",
                "sl",
                "tp",
                "so",
                "rollover",  # swap/rollover
                "reverse",  # reverse position
            }
        )
