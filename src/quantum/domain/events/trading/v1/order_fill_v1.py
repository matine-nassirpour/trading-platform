from typing import Literal

from quantum.domain.events.base import BaseEvent


class OrderFillV1(BaseEvent):
    event_name: Literal["order_fill_v1"] = "order_fill_v1"
    app: Literal["ea_mql5"]
    intent_id: str
    order_id: int
    deal_id: int
    symbol: str
    price: float
    volume: float
    commission: float
    swap: float
    profit: float
    reason: str  # MT5 ENUM_DEAL_REASON stringified
    fill_ms: int  # t_fill (unix ms)
    partial: bool
