from dataclasses import dataclass

from quantum.domain.risk.sizing.reason_codes.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.risk.sizing.states.position_sizing_pending_state import (
    PositionSizingPendingState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class PositionSizingRejectedState(PositionSizingPendingState):
    reason_code: PositionSizingRejectionReasonCode
    rejected_at: EpochMs

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.reason_code, PositionSizingRejectionReasonCode):
            raise InvariantViolation("PositionSizingRejectedState.reason_code invalid")

        if not isinstance(self.rejected_at, EpochMs):
            raise InvariantViolation("PositionSizingRejectedState.rejected_at invalid")

        if self.rejected_at.value < self.requested_at.value:
            raise InvariantViolation("rejected_at must be >= requested_at")
