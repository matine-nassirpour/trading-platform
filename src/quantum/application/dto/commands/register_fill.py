from dataclasses import dataclass

from quantum.domain.execution.value_objects.execution_cost import ExecutionCost
from quantum.domain.execution.value_objects.execution_fill import ExecutionFill
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class RegisterFillCommand:
    intent_id: IntentId
    order_id: OrderId
    execution_fill: ExecutionFill
    execution_cost: ExecutionCost | None = None
