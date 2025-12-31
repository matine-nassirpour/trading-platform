from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.value_objects.kill_switch_reason import KillSwitchReason
from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    event_version: ClassVar[int] = 1

    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
