from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.risk.kill_switch.detail import KillSwitchDetail
from quantum.domain.risk.kill_switch.reason import KillSwitchReason


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredEvent(RiskEvent):
    event_name: ClassVar[str] = "risk.killswitch.triggered"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: KillSwitchDetail | None = None
