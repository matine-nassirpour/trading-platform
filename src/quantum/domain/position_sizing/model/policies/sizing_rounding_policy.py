from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class SizingRoundingPolicy(ClosedSetValueObject):
    """
    Policy controlling how raw theoretical volume is converted into executable volume.

    floor_to_step:
        Conservative policy. Never increases risk. Rounds down to broker volume step.

    reject_if_not_exact:
        Strict policy. Rejects if theoretical size is not exactly executable.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "floor_to_step",
                "reject_if_not_exact",
            }
        )

    @classmethod
    def floor_to_step(cls) -> SizingRoundingPolicy:
        return cls("floor_to_step")

    @classmethod
    def reject_if_not_exact(cls) -> SizingRoundingPolicy:
        return cls("reject_if_not_exact")

    def floors_to_step(self) -> bool:
        return self.value == "floor_to_step"

    def rejects_if_not_exact(self) -> bool:
        return self.value == "reject_if_not_exact"
