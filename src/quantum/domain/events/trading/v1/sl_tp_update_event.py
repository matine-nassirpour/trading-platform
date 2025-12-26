from decimal import Decimal
from typing import ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


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
