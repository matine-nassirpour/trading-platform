from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.safety_control.events.safety_control_event import SafetyControlEvent
from quantum.domain.safety_control.kill_switch.kill_switch_detail import (
    KillSwitchDetail,
)
from quantum.domain.safety_control.kill_switch.kill_switch_reason import (
    KillSwitchReason,
)


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredEvent(SafetyControlEvent):
    event_name: ClassVar[str] = "safety_control.killswitch.triggered"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: KillSwitchDetail | None = None
