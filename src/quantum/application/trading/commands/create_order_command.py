from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.aggregate import OrderId
from quantum.domain.trading.order.order_kind import OrderKind
from quantum.domain.trading.order.time_in_force import TimeInForce


@dataclass(frozen=True, slots=True)
class CreateOrderCommand(BaseCommand):
    """
    Command: create a new Order aggregate stream.

    Domain consequence:
    - OrderCreatedEvent
    """

    order_id: OrderId
    decision_id: DecisionId
    broker_order_ref: BrokerOrderRef
    symbol: Symbol
    order_kind: OrderKind
    side: PositionSide
    volume: PositiveVolume
    reference_price: ReferencePrice | None = None
    stop_price: Price | None = None
    limit_price: Price | None = None
    sl: Price | None = None
    tp: Price | None = None
    time_in_force: TimeInForce | None = None
