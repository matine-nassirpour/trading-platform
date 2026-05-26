from dataclasses import dataclass

from quantum.domain.position_sizing.states.position_sizing_pending_state import (
    PositionSizingPendingState,
)
from quantum.domain.position_sizing.value_objects.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class PositionSizingSizedState(PositionSizingPendingState):
    result: PositionSizingResult
    sized_at: EpochMs

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.result, PositionSizingResult):
            raise InvariantViolation("PositionSizingSizedState.result invalid")

        if not isinstance(self.sized_at, EpochMs):
            raise InvariantViolation("PositionSizingSizedState.sized_at invalid")

        if self.sized_at.value < self.requested_at.value:
            raise InvariantViolation("sized_at must be >= requested_at")
