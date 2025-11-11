from typing import Protocol

from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult


class ExecutionOrchestratorPort(Protocol):
    """
    High-level orchestrator interface for multichannel execution routing.
    """

    def send_order(self, request: OrderRequest) -> ExecutionResult: ...
    def check_order(self, request: CheckRequest) -> ExecutionResult: ...
    def get_positions(self, request: QueryRequest) -> ExecutionResult: ...
    def get_orders(self, request: QueryRequest) -> ExecutionResult: ...
