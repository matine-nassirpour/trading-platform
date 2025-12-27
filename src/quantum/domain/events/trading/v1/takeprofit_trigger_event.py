from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import (
    DealId,
    IntentId,
    OrderId,
    PositionId,
)
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import PositiveVolume
from quantum.domain.types.enums import App, DealEntry, DealReason


@dataclass(frozen=True)
class TakeProfitTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.takeprofit_trigger"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Price
    tp_price: Price
    volume_closed: PositiveVolume

    trigger_epoch_ms: EpochMs
    deal_entry: DealEntry = DealEntry.OUT
    reason: DealReason = DealReason.TP
    app: App = App.EA_MQL5
