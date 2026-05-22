from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import PositiveVolume
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.aggregate import OrderId
from quantum.domain.trading.order.order_kind import OrderKind


@dataclass(frozen=True, slots=True)
class CreateOrderFromIntentCommand(BaseCommand):
    order_id: OrderId
    intent_id: DecisionId
    broker_order_ref: BrokerOrderRef
    symbol: Symbol
    order_kind: OrderKind
    side: PositionSide
    volume: PositiveVolume
