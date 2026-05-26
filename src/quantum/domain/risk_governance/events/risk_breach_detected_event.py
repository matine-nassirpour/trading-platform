from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.events.risk_governance_event import (
    RiskGovernanceEvent,
)


@dataclass(frozen=True, slots=True)
class RiskBreachDetectedEvent(RiskGovernanceEvent):
    """
    Emitted when a configured risk limit is breached.

    Payload is a fully typed ADT RiskBreach.
    """

    event_name: ClassVar[str] = "risk_governance.breach.detected"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
