from collections.abc import Mapping
from dataclasses import dataclass

from quantum.application.contracts.execution_result import ExecutionResult
from quantum.domain.types.execution_channel import ExecutionChannel


@dataclass(frozen=True)
class BroadcastResult:
    """
    Composite result for broadcast operations.
    """

    results: Mapping[ExecutionChannel, ExecutionResult]

    def succeeded(self) -> bool:
        """True if all executions succeeded."""
        return all(r.succeeded() for r in self.results.values())

    def failed_channels(self) -> list[ExecutionChannel]:
        return [ch for ch, res in self.results.items() if res.failed()]

    def summary(self) -> str:
        ok = sum(r.succeeded() for r in self.results.values())
        total = len(self.results)
        return f"{ok}/{total} executions succeeded"
