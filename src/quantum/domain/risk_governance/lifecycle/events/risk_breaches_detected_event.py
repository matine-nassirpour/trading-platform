from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskBreachesDetectedEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.breaches.detected"
    event_version: ClassVar[int] = 1

    breaches: tuple[RiskBreach, ...]

    def _validate_payload(self) -> None:
        if not isinstance(self.breaches, tuple):
            raise InvariantViolation("breaches must be tuple[RiskBreach, ...]")

        if not self.breaches:
            raise InvariantViolation(
                "RiskBreachesDetectedEvent requires at least one breach"
            )

        for breach in self.breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation("breaches must contain only RiskBreach")
