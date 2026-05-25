from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.limits.exposure_limit import ExposureLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.risk.governance.services.threshold_breach_detector import (
    ThresholdBreachDetector,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class ExposureBreach(RiskBreach):
    """
    Risk breach raised when exposure exceeds the allowed limit.

    Invariants:
    - current is an Exposure
    - limit is an ExposureLimit
    - both share the same MoneyContext
    """

    current: Exposure
    limit: ExposureLimit

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.current, Exposure):
            raise InvariantViolation("ExposureBreach.current must be an Exposure")

        if not isinstance(self.limit, ExposureLimit):
            raise InvariantViolation("ExposureBreach.limit must be an ExposureLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("Exposure MoneyContext mismatch")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        current: Exposure,
        limit: ExposureLimit,
        policy: RiskThresholdPolicy,
    ) -> ExposureBreach | None:
        return ThresholdBreachDetector.detect(
            current_value=current.value,
            limit_value=limit.value,
            policy=policy,
            breach_factory=lambda: ExposureBreach(
                current=current,
                limit=limit,
                policy=policy,
            ),
        )
