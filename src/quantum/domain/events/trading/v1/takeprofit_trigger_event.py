from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class TakeProfitTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.takeprofit_trigger"

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Decimal
    tp_price: Decimal
    volume_closed: Decimal
    trigger_epoch_ms: EpochMs
    deal_entry: DealEntry = DealEntry.OUT
    reason: DealReason = DealReason.TP
    app: App = App.EA_MQL5
