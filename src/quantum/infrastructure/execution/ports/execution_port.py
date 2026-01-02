from typing import Protocol

from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult


class ExecutionPort(Protocol):
    """
    Outbound port for execution systems (e.g., MetaTrader5, FIX, simulator).

    Defines the minimal contract required for the application layer to
    send trade intents, verify orders, and query execution state,
    independently of the underlying infrastructure.
    """

    def send_order(self, request: OrderRequest) -> ExecutionResult: ...

    def check_order(self, request: CheckRequest) -> ExecutionResult: ...

    def get_positions(self, request: QueryRequest) -> ExecutionResult: ...

    def get_orders(self, request: QueryRequest) -> ExecutionResult: ...
