from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.kill_switch.reason import KillSwitchReason
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredEvent(RiskEvent):
    event_name: ClassVar[str] = "risk.killswitch.triggered"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: str | None = None
