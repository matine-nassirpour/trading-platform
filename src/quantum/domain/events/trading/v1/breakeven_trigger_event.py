from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs, IntentId, PositionId, Symbol


class BreakevenTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.breakeven_trigger"
    app: App = App.EA_MQL5
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId | None = None
    trigger_epoch_ms: EpochMs
    price_at_trigger: Decimal
