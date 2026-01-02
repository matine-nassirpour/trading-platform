from dataclasses import dataclass

from quantum.domain.execution.value_objects.fill import Fill
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class RegisterFillCommand:
    order_id: OrderId
    fill: Fill
