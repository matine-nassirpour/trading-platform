from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breach_detection.breaches.threshold_risk_breach import (
    ThresholdRiskBreach,
)
from quantum.domain.risk_governance.limits.exposure_limit import ExposureLimit
from quantum.domain.risk_governance.portfolio_state.exposure import Exposure
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class ExposureBreach(ThresholdRiskBreach):
    """
    Risk breach raised when exposure exceeds the allowed limit.
    """

    current: Exposure
    limit: ExposureLimit

    CURRENT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = Exposure
    LIMIT_TYPE: ClassVar[type[ContextualMonetaryAmount]] = ExposureLimit
