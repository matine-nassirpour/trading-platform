from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import (
    DealId,
    IntentId,
    OrderId,
    PositionId,
)
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App, DealEntry, DealReason


class TakeProfitTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.takeprofit_trigger"
    app: App = App.EA_MQL5

    intent_id: IntentId | None = None
    order_id: OrderId | None = None
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Decimal
    tp_price: Decimal
    volume_closed: Decimal
    deal_entry: DealEntry = DealEntry.OUT
    reason: DealReason = DealReason.TP
    trigger_epoch_ms: EpochMs
