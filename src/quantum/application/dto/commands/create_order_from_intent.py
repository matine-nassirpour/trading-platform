from dataclasses import dataclass

from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class CreateOrderFromIntentCommand:
    intent_id: IntentId
    order_id: OrderId
    order_type: OrderType
    volume: PositiveVolume
    at: EpochMs
    sizing_model: str | None = None
