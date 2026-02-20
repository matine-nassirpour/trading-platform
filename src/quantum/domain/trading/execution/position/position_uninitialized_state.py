from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.trading.execution.position.position_state_base import (
    PositionStateBase,
)


@dataclass(frozen=True, slots=True)
class PositionUninitializedState(PositionStateBase):

    def _validate(self):
        if not self.last_sequence.is_initial():
            raise InvariantViolation("Uninitialized position must be initial")
