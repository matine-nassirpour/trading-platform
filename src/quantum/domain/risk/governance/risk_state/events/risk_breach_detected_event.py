from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class RiskBreachDetectedEvent(RiskEvent):
    """
    Emitted when a configured risk limit is breached.

    Payload is a fully typed ADT RiskBreach.
    """

    event_name: ClassVar[str] = "risk.breach.detected"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
