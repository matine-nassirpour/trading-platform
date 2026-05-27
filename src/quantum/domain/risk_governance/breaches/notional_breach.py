from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breaches.threshold_risk_breach import (
    ThresholdRiskBreach,
)
from quantum.domain.risk_governance.limits.notional_limit import NotionalLimit
from quantum.domain.risk_governance.measures.notional import Notional
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class NotionalBreach(ThresholdRiskBreach):
    """
    Risk breach for notional exposure limit violation.
    """

    current: Notional
    limit: NotionalLimit

    CURRENT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = Notional
    LIMIT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = NotionalLimit
