from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.serialization.schema_registry import register_event
from quantum.domain.types.enums import App, KillSwitchReason
from quantum.domain.value_objects import EpochMs


@register_event
class KillSwitchTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    app: App = App.EA_MQL5
    trigger_epoch_ms: EpochMs
    reason: KillSwitchReason
    detail: str | None = None
