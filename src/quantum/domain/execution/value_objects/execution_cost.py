from dataclasses import dataclass

from quantum.domain.execution.value_objects.execution_id import ExecutionId
from quantum.domain.execution.value_objects.fee import Fee
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
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
