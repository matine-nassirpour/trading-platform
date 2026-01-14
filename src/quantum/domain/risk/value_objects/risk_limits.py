from dataclasses import dataclass

from quantum.domain.risk.value_objects.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.risk.value_objects.notional import Notional
from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskLimits(ValueObject):
    """
    Canonical desk-level risk limits.

    Properties:
    - All limits are monetary thresholds
    - Limits are NOT algebraic quantities
    - All limits must share the same MoneyContext
    """

    context: MoneyContext
    max_drawdown: DrawdownLimit
    max_notional: Notional
    max_daily_loss: DailyLossLimit
    threshold_policy: RiskThresholdPolicy

    def _validate(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("RiskLimits requires a MoneyContext")

        if not isinstance(self.max_drawdown, DrawdownLimit):
            raise InvariantViolation("max_drawdown must be DrawdownLimit")

        if not isinstance(self.max_notional, Notional):
            raise InvariantViolation("max_notional must be Notional")

        if not isinstance(self.max_daily_loss, DailyLossLimit):
            raise InvariantViolation("max_daily_loss must be DailyLossLimit")

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if limit.context != self.context:
                raise InvariantViolation(
                    f"{name} MoneyContext mismatch: {limit.context} vs {self.context}"
                )

        if not isinstance(self.threshold_policy, RiskThresholdPolicy):
            raise InvariantViolation("RiskLimits requires a RiskThresholdPolicy")
