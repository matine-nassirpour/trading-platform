from decimal import Decimal
from typing import ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.serialization.schema_registry import register_event
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs, IntentId, PositionId, Symbol


@register_event
class SlTpUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.sl_tp_update"
    app: App = App.EA_MQL5
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId | None = None
    old_sl: Decimal | None = None
    new_sl: Decimal | None = None
    old_tp: Decimal | None = None
    new_tp: Decimal | None = None
    update_epoch_ms: EpochMs
    reason: Literal["manual", "rule", "risk"]
