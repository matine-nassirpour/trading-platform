from typing import Literal

from quantum.foundation.events.common.base import BaseEvent


class OrderSubmitV1(BaseEvent):
    event_name: Literal["order_submit_v1"] = "order_submit_v1"
    app: Literal["ea_mql5"]
    intent_id: str
    client_order_id: str
    symbol: str
    request_ms: int  # t_send (unix ms) on sending
    response_ms: int | None = None  # completed in the ACK
    request: dict  # snapshot of the MqlTradeRequest
