from typing import Protocol, runtime_checkable

from quantum.domain.trading.execution.reports.execution_report import ExecutionReport


@runtime_checkable
class ExecutionReportListener(Protocol):

    def on_execution_report(self, report: ExecutionReport) -> None:
        raise NotImplementedError
