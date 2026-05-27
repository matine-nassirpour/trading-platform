from dataclasses import dataclass

from quantum.domain.risk_governance.lifecycle.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskGovernanceInsolventState(RiskGovernanceInitializedState):
    """
    Terminal / frozen risk state.

    Once equity <= 0, the account is considered insolvent.
    No further trading-related evolution is allowed from this state.
    """

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.snapshot.equity.value > 0:
            raise InvariantViolation(
                "RiskGovernanceInsolventState requires equity <= 0"
            )
