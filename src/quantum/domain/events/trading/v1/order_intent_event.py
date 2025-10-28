from decimal import Decimal
from typing import ClassVar

from quantum.shared.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import App, OrderType, TimeInForce
from quantum.shared.types.value_objects import IntentId, Symbol


@register_event
class OrderIntentEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_intent"
    app: App

    intent_id: IntentId
    symbol: Symbol
    type: OrderType

    # Volume & prices
    volume: PositiveDecimal
    price: Decimal | None = None
    stop_price: Decimal | None = None
    limit_price: Decimal | None = None

    sl: Decimal | None = None
    tp: Decimal | None = None

    time_in_force: TimeInForce | None = TimeInForce.GTC
    rationale: str | None = None  # brief tag “setup”
