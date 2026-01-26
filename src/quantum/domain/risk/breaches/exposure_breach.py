from dataclasses import dataclass

from quantum.domain.risk.breaches.risk_breach import RiskBreach
from quantum.domain.risk.limits.exposure_limit import ExposureLimit
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure


@dataclass(frozen=True, slots=True)
class ExposureBreach(RiskBreach):
    """
    Risk breach raised when exposure exceeds the allowed limit.

    Invariants:
    - current is an Exposure
    - limit is an ExposureLimit
    - both share the same MoneyContext
    """

    current: RiskExposure
    limit: ExposureLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.current, RiskExposure):
            raise InvariantViolation("ExposureBreach.current must be an Exposure")

        if not isinstance(self.limit, ExposureLimit):
            raise InvariantViolation("ExposureBreach.limit must be an ExposureLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("Exposure MoneyContext mismatch")
