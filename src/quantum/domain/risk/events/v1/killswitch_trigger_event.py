from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.value_objects.kill_switch_reason import KillSwitchReason
from quantum.domain.shared_kernel.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: str | None = None
