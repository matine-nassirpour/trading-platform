from dataclasses import dataclass

from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.risk_governance.measures.drawdown import Drawdown
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.measures.exposure import Exposure
from quantum.domain.risk_governance.measures.notional import Notional
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
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
        expected_context = self.equity.context
        expected_currency = self.equity.currency

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

            if value.context != expected_context:
                raise InvariantViolation(f"RiskSnapshot.{name} MoneyContext mismatch")

            if value.currency != expected_currency:
                raise CurrencyMismatch(f"RiskSnapshot.{name} currency mismatch")

        if self.equity_peak.value < self.equity.value:
            raise InvariantViolation("equity_peak must be >= equity")

        expected_drawdown = self.equity_peak.value - self.equity.value

        if self.drawdown.value != expected_drawdown:
            raise InvariantViolation("drawdown must equal equity_peak - equity")
