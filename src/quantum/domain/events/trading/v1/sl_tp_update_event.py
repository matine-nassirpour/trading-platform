from decimal import Decimal
from typing import ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App
from quantum.shared.types.time import EpochMs


@register_event
class SlTpUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.sl_tp_update"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    old_sl: Decimal | None = None
    new_sl: Decimal | None = None
    old_tp: Decimal | None = None
    new_tp: Decimal | None = None
    update_epoch_ms: EpochMs
    reason: Literal["manual", "rule", "risk"]
