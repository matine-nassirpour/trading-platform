from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App
from quantum.shared.types.time import EpochMs


@register_event
class BreakevenTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.breakeven_trigger"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    trigger_epoch_ms: EpochMs
    price_at_trigger: Decimal
