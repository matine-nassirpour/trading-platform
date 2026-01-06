from dataclasses import dataclass

from quantum.domain.trading.execution.analytics.execution_report import ExecutionReport


@dataclass(frozen=True)
class RegisterExecutionReportCommand:
    report: ExecutionReport
