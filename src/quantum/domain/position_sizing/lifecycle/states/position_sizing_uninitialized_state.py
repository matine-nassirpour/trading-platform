from dataclasses import dataclass

from quantum.domain.position_sizing.lifecycle.states.position_sizing_state_base import (
    PositionSizingStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class PositionSizingUninitializedState(PositionSizingStateBase):
    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized PositionSizing must have initial sequence"
            )
