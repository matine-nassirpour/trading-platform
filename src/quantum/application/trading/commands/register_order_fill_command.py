from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill


@dataclass(frozen=True, slots=True)
class RegisterOrderFillCommand:
    order_id: OrderId
    fill: ExecutionFill
