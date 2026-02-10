from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.order_id import OrderId


@dataclass(frozen=True, slots=True)
class CancelOrderCommand:
    order_id: OrderId
