from typing import Literal

from quantum.foundation.events.common.base import BaseEvent


class OrderAckV1(BaseEvent):
    event_name: Literal["order_ack_v1"] = "order_ack_v1"
    app: Literal["ea_mql5"]
    intent_id: str
    client_order_id: str
    order_id: int | None = None
    symbol: str
    ack_ms: int  # t_ack (unix ms)
