from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.trading.execution.order.execution_id import ExecutionId
from quantum.domain.trading.execution.settlement.fee import Fee


@dataclass(frozen=True, slots=True)
class ExecutionCost(ValueObject):
    """
    Financial impact associated with an execution.

    Explicitly separated from the economic fill.
    """

    execution_id: ExecutionId
    fee: Fee

    def _validate(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("ExecutionCost requires a valid ExecutionId")

        if not isinstance(self.fee, Fee):
            raise InvariantViolation("ExecutionCost requires a valid Fee")
