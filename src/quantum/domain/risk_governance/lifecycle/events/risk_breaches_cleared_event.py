from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)


@dataclass(frozen=True, slots=True)
class RiskBreachesClearedEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.breaches.cleared"
    event_version: ClassVar[int] = 1
