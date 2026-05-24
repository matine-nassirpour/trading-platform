from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.execution.fills.execution_id import ExecutionId
from quantum.domain.trading.execution.reports.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.trading.execution.taxonomy.execution_type import ExecutionType


@dataclass(frozen=True, slots=True)
class ExecutionReport(ValueObject):
    """
    Canonical execution report.

    Mirrors FIX ExecReport semantics without infra coupling.
    """

    execution_id: ExecutionId
    execution_type: ExecutionType
    reported_at: EpochMs
    rejection: ExecutionRejection | None = None

    def _validate_semantics(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise InvariantViolation("ExecutionReport must have a valid ExecutionId")

        if not isinstance(self.execution_type, ExecutionType):
            raise InvariantViolation("ExecutionReport must have a valid ExecutionType")

        if not isinstance(self.reported_at, EpochMs):
            raise InvariantViolation("ExecutionReport must have a valid timestamp")

        if self.rejection is not None and not isinstance(
            self.rejection,
            ExecutionRejection,
        ):
            raise InvariantViolation(
                "ExecutionReport.rejection must be ExecutionRejection or None"
            )

        if self.execution_type == ExecutionType.reject():
            if self.rejection is None:
                raise InvariantViolation(
                    "Rejected ExecutionReport requires ExecutionRejection"
                )
        else:
            if self.rejection is not None:
                raise InvariantViolation(
                    "ExecutionReport.rejection is allowed only for reject reports"
                )
