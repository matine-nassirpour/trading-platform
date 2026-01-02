from dataclasses import dataclass

from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: OrderId
