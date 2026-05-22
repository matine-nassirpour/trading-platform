from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.trading.position.states.position_state_base import PositionStateBase


@dataclass(frozen=True, slots=True)
class PositionUninitializedState(PositionStateBase):

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation("Uninitialized position must be initial")
