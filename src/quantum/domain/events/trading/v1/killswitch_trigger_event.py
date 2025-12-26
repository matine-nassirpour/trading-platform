from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects import EpochMs
from quantum.domain.types.enums import App, KillSwitchReason


class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    app: App = App.EA_MQL5
    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
