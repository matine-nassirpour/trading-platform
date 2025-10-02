from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class OrderSubmitEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_submit"
    app: App = App.EA_MQL5
    intent_id: str
    client_order_id: str
    symbol: str
    request_ms: int  # t_send (unix ms) on sending
    response_ms: int | None = None  # completed in the ACK
    request: dict  # snapshot of the MqlTradeRequest
