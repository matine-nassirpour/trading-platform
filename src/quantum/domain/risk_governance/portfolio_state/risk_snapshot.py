from dataclasses import dataclass

from quantum.domain.risk_governance.breach_detection.monetary_compatibility import (
    MonetaryCompatibilityService,
)
from quantum.domain.risk_governance.portfolio_state.daily_loss import DailyLoss
from quantum.domain.risk_governance.portfolio_state.drawdown import Drawdown
from quantum.domain.risk_governance.portfolio_state.equity import Equity
from quantum.domain.risk_governance.portfolio_state.exposure import Exposure
from quantum.domain.risk_governance.portfolio_state.notional import Notional
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskSnapshot(ValueObject):
    equity: Equity
    equity_peak: Equity
    drawdown: Drawdown
    daily_loss: DailyLoss
    exposure: Exposure
    notional: Notional

    def _validate_semantics(self) -> None:
        if not isinstance(self.equity, Equity):
            raise InvariantViolation("RiskSnapshot.equity invalid")

        values = (
            ("equity_peak", self.equity_peak, Equity),
            ("drawdown", self.drawdown, Drawdown),
            ("daily_loss", self.daily_loss, DailyLoss),
            ("exposure", self.exposure, Exposure),
            ("notional", self.notional, Notional),
        )

        for name, value, expected_type in values:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"RiskSnapshot.{name} invalid")

            MonetaryCompatibilityService.assert_same_context_and_currency(
                left=self.equity,
                right=value,
                left_label="RiskSnapshot.equity",
                right_label=f"RiskSnapshot.{name}",
            )

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("equity_peak must be >= equity")

        expected_drawdown = self.equity_peak.value - self.equity.value

        if self.drawdown.value != expected_drawdown:
            raise InvariantViolation("drawdown must equal equity_peak - equity")
