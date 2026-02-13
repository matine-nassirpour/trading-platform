from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.trading.execution.analytics.execution_report import ExecutionReport


@runtime_checkable
class ExecutionReportListener(Protocol):

    @abstractmethod
    def on_execution_report(self, report: ExecutionReport) -> None:
        raise NotImplementedError
