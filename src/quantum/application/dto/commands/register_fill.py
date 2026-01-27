from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.execution.settlement.execution_cost import ExecutionCost


@dataclass(frozen=True)
class RegisterFillCommand:
    intent_id: IntentId
    order_id: OrderId
    execution_fill: ExecutionFill
    execution_cost: ExecutionCost | None = None
