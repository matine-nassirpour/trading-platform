from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.safety_control.detail import KillSwitchDetail
from quantum.domain.safety_control.events.safety_event import SafetyEvent
from quantum.domain.safety_control.reason import KillSwitchReason


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredEvent(SafetyEvent):
    event_name: ClassVar[str] = "risk.killswitch.triggered"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: KillSwitchDetail | None = None
