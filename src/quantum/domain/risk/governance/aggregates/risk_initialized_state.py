from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.risk_state_base import RiskStateBase
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.equity import Equity


@dataclass(frozen=True, slots=True)
class RiskInitializedState(RiskStateBase):

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    def _validate(self):
        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized risk cannot be initial")
