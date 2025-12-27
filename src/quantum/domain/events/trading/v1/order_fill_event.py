from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import DealId, IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App, DealEntry, DealReason


@dataclass(frozen=True)
class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    symbol: Symbol

    price: Decimal
    volume: Decimal
    commission: Decimal
    swap: Decimal
    profit: Decimal

    cum_volume: Decimal
    leaves_volume: Decimal

    deal_entry: DealEntry
    reason: DealReason
    fill_epoch_ms: EpochMs  # t_fill (unix ms)
    partial: bool
    app: App = App.EA_MQL5
