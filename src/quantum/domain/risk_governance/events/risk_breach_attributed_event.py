from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.attribution.risk_attribution import RiskAttribution
from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.events.risk_governance_event import (
    RiskGovernanceEvent,
)


@dataclass(frozen=True, slots=True)
class RiskBreachAttributedEvent(RiskGovernanceEvent):
    """
    Emitted to explicitly attribute the origin of a detected risk.
    """

    event_name: ClassVar[str] = "risk_governance.breach.attributed"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    attribution: RiskAttribution
