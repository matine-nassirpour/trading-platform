from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import PositiveVolume
from quantum.domain.types.enums import App, OrderType, TimeInForce


@dataclass(frozen=True)
class OrderIntentEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_intent"
    event_version: ClassVar[int] = 1
    app: App

    intent_id: IntentId
    symbol: Symbol
    type: OrderType

    volume: PositiveVolume
    price: Price
    stop_price: Price | None = None
    limit_price: Price | None = None

    sl: Price | None = None
    tp: Price | None = None

    time_in_force: TimeInForce | None = TimeInForce.GTC
    rationale: str | None = None  # brief tag “setup”
