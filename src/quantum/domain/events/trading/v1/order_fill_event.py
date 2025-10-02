from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"
    app: App = App.EA_MQL5
    intent_id: str
    order_id: int
    deal_id: int
    symbol: str
    price: Decimal
    volume: Decimal
    commission: Decimal
    swap: Decimal
    profit: Decimal
    reason: str  # MT5 ENUM_DEAL_REASON stringified
    fill_ms: int  # t_fill (unix ms)
    partial: bool
