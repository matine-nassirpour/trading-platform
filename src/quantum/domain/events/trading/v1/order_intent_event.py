from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, OrderType, Side, TimeInForce


class OrderIntentEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_intent"
    app: App
    intent_id: str
    symbol: str
    side: Side
    type: OrderType
    volume: Decimal
    price: Decimal | None = None
    sl: Decimal | None = None
    tp: Decimal | None = None
    time_in_force: TimeInForce | None = TimeInForce.GTC
    client_order_id: str | None = None
    rationale: str | None = None  # brief tag “setup”
