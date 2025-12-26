from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.types.decimal_validators import PositiveDecimal
from quantum.domain.types.enums import App, OrderType, TimeInForce


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
