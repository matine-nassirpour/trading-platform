from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import DealId, IntentId, OrderId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.enums import App, DealEntry, DealReason


@dataclass(frozen=True)
class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    symbol: Symbol

    price: Price
    volume: Volume
    commission: Money
    swap: Money
    profit: Money

    deal_entry: DealEntry
    reason: DealReason
    fill_epoch_ms: EpochMs  # t_fill (unix ms)
    partial: bool
    app: App = App.EA_MQL5
