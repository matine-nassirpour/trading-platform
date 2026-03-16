from dataclasses import dataclass

from quantum.domain.risk.governance.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.governance.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk.governance.limits.exposure_limit import ExposureLimit
from quantum.domain.risk.governance.limits.leverage_limit import LeverageLimit
from quantum.domain.risk.governance.limits.notional_limit import NotionalLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
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
    max_notional: NotionalLimit
    max_daily_loss: DailyLossLimit
    max_exposure: ExposureLimit
    max_leverage: LeverageLimit

    threshold_policy: RiskThresholdPolicy

    def _validate_types(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("RiskLimits requires a MoneyContext")

        if not isinstance(self.max_drawdown, DrawdownLimit):
            raise InvariantViolation("max_drawdown must be DrawdownLimit")

        if not isinstance(self.max_notional, NotionalLimit):
            raise InvariantViolation("max_notional must be NotionalLimit")

        if not isinstance(self.max_daily_loss, DailyLossLimit):
            raise InvariantViolation("max_daily_loss must be DailyLossLimit")

        if not isinstance(self.max_exposure, ExposureLimit):
            raise InvariantViolation("RiskLimits requires a ExposureLimit")

        if not isinstance(self.max_leverage, LeverageLimit):
            raise InvariantViolation("RiskLimits requires a LeverageLimit")

        if not isinstance(self.threshold_policy, RiskThresholdPolicy):
            raise InvariantViolation("RiskLimits requires a RiskThresholdPolicy")

    def _validate(self) -> None:
        self._validate_types()

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
            "max_exposure": self.max_exposure,
        }.items():
            if limit.context != self.context:
                raise InvariantViolation(
                    f"{name} MoneyContext mismatch: {limit.context} vs {self.context}"
                )
