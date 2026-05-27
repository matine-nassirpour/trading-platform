from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breach_detection.breaches.threshold_risk_breach import (
    ThresholdRiskBreach,
)
from quantum.domain.risk_governance.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk_governance.portfolio_state.daily_loss import DailyLoss
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class DailyLossBreach(ThresholdRiskBreach):
    """
    Risk breach for daily realized loss limit violation.
    """

    current: DailyLoss
    limit: DailyLossLimit

    CURRENT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = DailyLoss
    LIMIT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = DailyLossLimit
