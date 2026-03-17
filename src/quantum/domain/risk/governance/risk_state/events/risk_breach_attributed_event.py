from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.risk.governance.risk_state.attribution.risk_attribution import (
    RiskAttribution,
)
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach


@dataclass(frozen=True, slots=True)
class RiskBreachAttributedEvent(RiskEvent):
    """
    Emitted to explicitly attribute the origin of a detected risk.
    """

    event_name: ClassVar[str] = "risk.breach.attributed"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    attribution: RiskAttribution
