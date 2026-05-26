from dataclasses import dataclass

from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.states.risk_governance_state_base import (
    RiskGovernanceStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)


@dataclass(frozen=True, slots=True)
class RiskGovernanceInitializedState(RiskGovernanceStateBase):

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    def _validate_types(self) -> None:
        if not isinstance(self.limits, RiskLimits):
            raise InvariantViolation(
                "RiskGovernanceInitializedState requires RiskLimits"
            )

        if not isinstance(self.equity, Equity):
            raise InvariantViolation("RiskGovernanceInitializedState requires Equity")

        if not isinstance(self.equity_peak, Equity):
            raise InvariantViolation(
                "RiskGovernanceInitializedState requires Equity peak"
            )

    def _validate_semantics(self) -> None:
        super()._validate_semantics()
        self._validate_types()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized risk cannot be initial")

        if self.equity.context != self.equity_peak.context:
            raise InvariantViolation("Equity and equity_peak MoneyContext mismatch")

        if self.equity.currency != self.equity_peak.currency:
            raise CurrencyMismatch("Equity and equity_peak currency mismatch")

        if self.limits.context != self.equity.context:
            raise InvariantViolation(
                "RiskLimits MoneyContext must match Equity MoneyContext"
            )

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("equity_peak must be >= equity")
