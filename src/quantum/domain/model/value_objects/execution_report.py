from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.execution_id import ExecutionId
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.execution import ExecutionType


@dataclass(frozen=True)
class ExecutionReport:
    """
    Canonical execution report.

    Mirrors FIX ExecReport semantics without infra coupling.
    """

    execution_id: ExecutionId
    execution_type: ExecutionType
    reason: str | None
    reported_at: EpochMs

    def __post_init__(self) -> None:
        if self.reason is not None and not self.reason.strip():
            raise InvariantViolation("ExecutionReport reason must not be empty")
