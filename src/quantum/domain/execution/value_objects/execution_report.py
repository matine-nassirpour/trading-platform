from dataclasses import dataclass

from quantum.domain.execution.types.execution_type import ExecutionType
from quantum.domain.execution.value_objects.execution_id import ExecutionId
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class ExecutionReport(ValueObject):
    """
    Canonical execution report.

    Mirrors FIX ExecReport semantics without infra coupling.
    """

    execution_id: ExecutionId
    execution_type: ExecutionType
    reason: str | None
    reported_at: EpochMs

    def _validate(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("ExecutionReport must have a valid ExecutionId")

        if not isinstance(self.execution_type, ExecutionType):
            raise InvariantViolation("ExecutionReport must have a valid ExecutionType")

        if self.reason is not None:
            if not isinstance(self.reason, str):
                raise InvariantViolation("ExecutionReport reason must be a string")
            if not self.reason.strip():
                raise InvariantViolation("ExecutionReport reason must not be empty")

        if not isinstance(self.reported_at, EpochMs):
            raise InvariantViolation("ExecutionReport must have a valid timestamp")
