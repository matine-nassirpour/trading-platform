from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import KillSwitchReason


@dataclass(frozen=True)
class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    event_version: ClassVar[int] = 1
    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
