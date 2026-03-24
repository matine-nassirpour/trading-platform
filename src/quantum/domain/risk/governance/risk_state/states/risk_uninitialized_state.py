from dataclasses import dataclass

from quantum.domain.risk.governance.risk_state.states.risk_state_base import (
    RiskStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskUninitializedState(RiskStateBase):
    """
    Aggregate state before RiskInitializedEvent has been applied.
    """

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized RiskState must have initial sequence"
            )
