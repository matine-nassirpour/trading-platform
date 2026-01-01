from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.market.price import Price
from quantum.domain.trading.value_objects.market.reference_price import ReferencePrice
from quantum.domain.trading.value_objects.market.volume import PositiveVolume
from quantum.domain.trading.value_objects.order.order_type import OrderType
from quantum.domain.trading.value_objects.order.time_in_force import TimeInForce


@dataclass(frozen=True)
class OrderIntentEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_intent"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    type: OrderType

    volume: PositiveVolume
    reference_price: ReferencePrice | None = None
    stop_price: Price | None = None
    limit_price: Price | None = None

    sl: Price | None = None
    tp: Price | None = None

    time_in_force: TimeInForce = TimeInForce("gtc")
    rationale: str | None = None  # brief tag “setup”
