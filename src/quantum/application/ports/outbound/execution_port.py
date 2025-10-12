from typing import Any, Protocol

from quantum.shared.types.execution import ExecutionCode


class ExecutionPort(Protocol):
    """
    Outbound port for execution systems (e.g., MetaTrader5, FIX, simulator).

    Defines the minimal contract required for the application layer to
    send trade intents, verify orders, and query execution state,
    independently of the underlying infrastructure.
    """

    def send_order(
        self, request: dict[str, Any]
    ) -> tuple[ExecutionCode, str, Any | None]: ...

    def check_order(
        self, request: dict[str, Any]
    ) -> tuple[ExecutionCode, str, Any | None]: ...

    def get_positions(
        self, symbol: str | None = None
    ) -> tuple[ExecutionCode, str, Any | None]: ...

    def get_orders(
        self, symbol: str | None = None
    ) -> tuple[ExecutionCode, str, Any | None]: ...
