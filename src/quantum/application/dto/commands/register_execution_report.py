from dataclasses import dataclass

from quantum.domain.execution.value_objects.execution_report import ExecutionReport


@dataclass(frozen=True)
class RegisterExecutionReportCommand:
    report: ExecutionReport
