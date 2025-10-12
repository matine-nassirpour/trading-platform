from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, KillSwitchReason
from quantum.shared.types.time import EpochMs


class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    app: App = App.EA_MQL5
    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
