from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import App, OrderType, Side, TimeInForce
from quantum.shared.types.value_objects import IntentId, Symbol


@register_event
class OrderIntentEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_intent"
    app: App

    intent_id: IntentId
    symbol: Symbol
    side: Side
    type: OrderType

    # Volume & prices
    volume: PositiveDecimal
    price: Decimal | None = None  # LIMIT
    stop_price: Decimal | None = None  # STOP / STOP_LIMIT (trigger)
    limit_price: Decimal | None = None  # STOP_LIMIT (limit price after trigger)

    sl: Decimal | None = None
    tp: Decimal | None = None

    time_in_force: TimeInForce | None = TimeInForce.GTC
    rationale: str | None = None  # brief tag “setup”

    @field_validator("price", "stop_price", "limit_price")
    @classmethod
    def _price_matrix(cls, v: Decimal | None, info):
        typ: OrderType | None = info.data.get("type")

        req_limit = typ == OrderType.LIMIT
        req_stop = typ == OrderType.STOP
        req_stop_l = typ == OrderType.STOP_LIMIT

        price = info.data.get("price")
        stop_price = info.data.get("stop_price")
        limit_price = info.data.get("limit_price")

        if typ == OrderType.MARKET:
            if any(x is not None for x in (price, stop_price, limit_price)):
                raise ValueError("MARKET must not define price/stop_price/limit_price")
        elif req_limit:
            if price is None:
                raise ValueError("LIMIT requires price")
            if any(x is not None for x in (stop_price, limit_price)):
                raise ValueError("LIMIT must not define stop_price/limit_price")
        elif req_stop:
            if stop_price is None:
                raise ValueError("STOP requires stop_price")
            if any(x is not None for x in (price, limit_price)):
                raise ValueError("STOP must not define price/limit_price")
        elif req_stop_l:
            if stop_price is None or limit_price is None:
                raise ValueError("STOP_LIMIT requires stop_price and limit_price")
            if price is not None:
                raise ValueError("STOP_LIMIT must not define price")

        return v
