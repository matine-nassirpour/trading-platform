from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class CreateOrderFromIntentCommand(BaseCommand):
    intent_id: IntentId
    broker_order_id: BrokerOrderId
    symbol: Symbol
    order_type: OrderType
    side: PositionSide
    volume: PositiveVolume
