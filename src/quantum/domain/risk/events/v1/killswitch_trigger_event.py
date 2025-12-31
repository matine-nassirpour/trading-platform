from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.types.enums import KillSwitchReason


@dataclass(frozen=True)
class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    event_version: ClassVar[int] = 1
    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
