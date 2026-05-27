from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breaches.threshold_risk_breach import (
    ThresholdRiskBreach,
)
from quantum.domain.risk_governance.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk_governance.measures.drawdown import Drawdown
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class DrawdownBreach(ThresholdRiskBreach):
    """
    Risk breach for drawdown limit violation.
    """

    current: Drawdown
    limit: DrawdownLimit

    CURRENT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = Drawdown
    LIMIT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = DrawdownLimit
