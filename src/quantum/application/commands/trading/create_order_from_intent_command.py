from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType


@dataclass(frozen=True, slots=True)
class CreateOrderFromIntentCommand:
    intent_id: IntentId
    order_id: OrderId
    order_type: OrderType
    volume: PositiveVolume
