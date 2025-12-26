from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects import EpochMs, IntentId, OrderId, Symbol
from quantum.domain.types.enums import App


class OrderAckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_ack"
    app: App = App.EA_MQL5
    intent_id: IntentId
    order_id: OrderId | None = None
    symbol: Symbol
    ack_epoch_ms: EpochMs
