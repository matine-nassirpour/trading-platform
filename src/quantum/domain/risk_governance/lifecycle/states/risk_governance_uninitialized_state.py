from dataclasses import dataclass

from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskGovernanceUninitializedState(RiskGovernanceStateBase):
    """
    Aggregate state before RiskInitializedEvent has been applied.
    """

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized RiskGovernanceState must have initial sequence"
            )
