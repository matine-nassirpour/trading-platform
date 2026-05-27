from dataclasses import dataclass

from quantum.domain.risk_governance.attribution.risk_reference import RiskReference
from quantum.domain.risk_governance.breach_detection.monetary_compatibility import (
    MonetaryCompatibilityService,
)
from quantum.domain.risk_governance.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk_governance.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk_governance.limits.exposure_limit import ExposureLimit
from quantum.domain.risk_governance.limits.leverage_limit import LeverageLimit
from quantum.domain.risk_governance.limits.notional_limit import NotionalLimit
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskLimits(ValueObject):
    """
    Canonical risk limits for one explicit risk scope.

    One RiskLimits instance applies to exactly one:
    - risk scope
    - monetary context
    - threshold policy
    """

    reference: RiskReference
    context: MoneyContext

    max_drawdown: DrawdownLimit
    max_notional: NotionalLimit
    max_daily_loss: DailyLossLimit
    max_exposure: ExposureLimit
    max_leverage: LeverageLimit

    threshold_policy: RiskThresholdPolicy

    def _validate_semantics(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("reference", self.reference, RiskReference),
            ("context", self.context, MoneyContext),
            ("max_drawdown", self.max_drawdown, DrawdownLimit),
            ("max_notional", self.max_notional, NotionalLimit),
            ("max_daily_loss", self.max_daily_loss, DailyLossLimit),
            ("max_exposure", self.max_exposure, ExposureLimit),
            ("max_leverage", self.max_leverage, LeverageLimit),
            ("threshold_policy", self.threshold_policy, RiskThresholdPolicy),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"RiskLimits.{field_name} invalid")

        contextual_limits = {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
            "max_exposure": self.max_exposure,
        }

        for name, limit in contextual_limits.items():
            MonetaryCompatibilityService.assert_reporting_currency(
                value=limit,
                expected_context=self.context,
                label=f"RiskLimits.{name}",
            )
