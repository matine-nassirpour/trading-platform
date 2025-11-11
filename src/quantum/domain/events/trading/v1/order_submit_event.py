from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.serialization.schema_registry import register_event
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs, IntentId, Symbol


@register_event
class OrderSubmitEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_submit"
    app: App = App.EA_MQL5
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs | None = None  # completed in the ACK
    request: dict[str, Any]  # snapshot of the MqlTradeRequest
