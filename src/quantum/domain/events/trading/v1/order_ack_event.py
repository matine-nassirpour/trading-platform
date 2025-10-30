from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App
from quantum.shared.types.value_objects import EpochMs, IntentId, OrderId, Symbol


@register_event
class OrderAckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_ack"
    app: App = App.EA_MQL5

    intent_id: IntentId
    order_id: OrderId | None = None
    symbol: Symbol
    ack_epoch_ms: EpochMs
