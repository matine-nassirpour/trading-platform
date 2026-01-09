from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.market.reference_price import ReferencePrice


@dataclass(frozen=True)
class OrderCreatedEvent(BaseEvent):
    """
    Emitted when an order is created inside a TradingIntent.

    Audit meaning:
    - The system decided to expose capital
    - With a specific side and order type
    """

    event_name: ClassVar[str] = "trading.order_created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    symbol: Symbol

    order_type: OrderType
    side: PositionSide
    volume: PositiveVolume

    reference_price: ReferencePrice | None = (
        None  # Non-executable price observed at decision time (audit / validation anchor)
    )
    stop_price: Price | None = (
        None  # Executable trigger price for STOP or STOP-LIMIT orders
    )
    limit_price: Price | None = (
        None  # Executable price constraint for LIMIT or STOP-LIMIT orders
    )

    sl: Price | None = None
    tp: Price | None = None

    time_in_force: TimeInForce = TimeInForce("gtc")
