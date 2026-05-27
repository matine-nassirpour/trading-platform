from dataclasses import dataclass

from quantum.domain.risk_governance.lifecycle.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)


@dataclass(frozen=True, slots=True)
class RiskGovernanceInitializedState(RiskGovernanceStateBase):

    limits: RiskLimits
    snapshot: RiskSnapshot

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.limits, RiskLimits):
            raise InvariantViolation(
                "RiskGovernanceInitializedState requires RiskLimits"
            )

        if not isinstance(self.snapshot, RiskSnapshot):
            raise InvariantViolation(
                "RiskGovernanceInitializedState requires RiskSnapshot"
            )

        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized risk cannot be initial")

        if self.limits.context != self.snapshot.equity.context:
            raise InvariantViolation(
                "RiskLimits MoneyContext must match RiskSnapshot MoneyContext"
            )

        if self.snapshot.equity.currency != self.limits.context.reporting_currency:
            raise CurrencyMismatch(
                "RiskSnapshot currency must equal RiskLimits.context.reporting_currency"
            )
