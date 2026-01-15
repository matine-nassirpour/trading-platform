from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class TimeInForce(ClosedSetValueObject):

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "gtc",
                "day",
                "specified",
                "specified_day",
            }
        )
