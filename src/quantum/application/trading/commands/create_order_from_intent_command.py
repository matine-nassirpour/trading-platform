from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId
from quantum.domain.trading.execution.order.order import OrderId
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class CreateOrderFromIntentCommand(BaseCommand):
    order_id: OrderId
    intent_id: IntentId
    broker_order_id: BrokerOrderId
    symbol: Symbol
    order_type: OrderType
    side: PositionSide
    volume: PositiveVolume
