from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.risk_state_base import RiskStateBase
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.risk.value_objects.equity import Equity
from quantum.domain.shared_kernel.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)


@dataclass(frozen=True, slots=True)
class RiskInitializedState(RiskStateBase):

    limits: RiskLimits
    equity: Equity
    equity_peak: Equity

    def _validate_types(self) -> None:
        if not isinstance(self.limits, RiskLimits):
            raise InvariantViolation("RiskInitializedState requires RiskLimits")

        if not isinstance(self.equity, Equity):
            raise InvariantViolation("RiskInitializedState requires Equity")

        if not isinstance(self.equity_peak, Equity):
            raise InvariantViolation("RiskInitializedState requires Equity peak")

    def _validate(self) -> None:
        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized risk cannot be initial")

        self._validate_types()

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
