from dataclasses import dataclass

from quantum.domain.risk.breaches.risk_breach import RiskBreach
from quantum.domain.risk.limits.leverage_limit import LeverageLimit
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.equity import Equity
from quantum.domain.shared_kernel.money.exposure import Exposure


@dataclass(frozen=True, slots=True)
class LeverageBreach(RiskBreach):
    """
    Risk breach raised when effective leverage exceeds allowed limit.

    Leverage is defined as:
        exposure / equity

    This breach indicates excessive capital amplification.
    """

    exposure: Exposure
    equity: Equity
    limit: LeverageLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.exposure, Exposure):
            raise InvariantViolation("LeverageBreach.exposure must be Exposure")

        if not isinstance(self.limit, LeverageLimit):
            raise InvariantViolation("LeverageBreach.limit must be LeverageLimit")

        if not isinstance(self.equity, Equity):
            raise InvariantViolation("LeverageBreach.equity must be Decimal")

        if self.exposure.context != self.equity.context:
            raise InvariantViolation("Exposure context mismatch")

        if self.equity.value <= 0:
            raise InvariantViolation("Equity must be strictly positive")
