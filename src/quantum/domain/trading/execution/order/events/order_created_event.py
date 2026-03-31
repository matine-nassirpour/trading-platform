from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class OrderCreatedEvent(FactEvent):
    """
    Emitted when an order is created inside a TradingIntent.

    Audit meaning:
    - The system decided to expose capital
    - With a specific side and order type
    """

    event_name: ClassVar[str] = "trading.order.created"
    event_version: ClassVar[int] = 1

    intent_id: DecisionId
    broker_order_id: BrokerOrderId
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
