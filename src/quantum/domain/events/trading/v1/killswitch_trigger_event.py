from typing import ClassVar

from pydantic import Field

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, KillSwitchReason
from quantum.shared.typing.time import EpochMs


class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    app: App = App.EA_MQL5
    trigger_epoch_ms: EpochMs = Field(alias="trigger_ms")
    reason: KillSwitchReason
    detail: str | None = None
