from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

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

    @field_validator("volume")
    @classmethod
    def _volume_positive(cls, v: Decimal):
        if v <= 0:
            raise ValueError("volume must be > 0")
        return v @ field_validator("price")

    @classmethod
    def _price_consistency(cls, v: Decimal | None, info):
        typ: OrderType | None = info.data.get("types")
        if typ in {OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT} and v is None:
            raise ValueError(f"price required for {typ}")
        if typ == OrderType.MARKET and v is not None:
            raise ValueError("price must be None for MARKET")
        return v
