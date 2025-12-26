from __future__ import annotations

from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects import (
    DealId,
    EpochMs,
    IntentId,
    OrderId,
    PositionId,
    Symbol,
)
from quantum.domain.types.decimal_validators import PositiveDecimal
from quantum.domain.types.enums import App, DealEntry, DealReason


class StopLossTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.stoploss_trigger"
    app: App = App.EA_MQL5

    intent_id: IntentId | None = None
    order_id: OrderId | None = None
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: PositiveDecimal
    sl_price: PositiveDecimal
    volume_closed: PositiveDecimal
    deal_entry: DealEntry = DealEntry.OUT
    reason: DealReason = DealReason.SL
    trigger_epoch_ms: EpochMs
