from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.governance.attribution.risk_attribution import RiskAttribution
from quantum.domain.risk.governance.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class RiskBreachAttributedEvent(RiskEvent):
    """
    Emitted to explicitly attribute the origin of a detected risk.
    """

    event_name: ClassVar[str] = "risk.breach.attributed"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    attribution: RiskAttribution
