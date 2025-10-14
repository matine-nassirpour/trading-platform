import logging

from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.adapters.mt5_exec")


class Mt5ExecutionAdapterImpl:
    """
    Concrete implementation of the ExecutionPort using the MT5 gateway.

    This adapter bridges the application layer and the MetaTrader5
    infrastructure through a unified and instrumented gateway interface.
    """

    def __init__(self, channel: ExecutionChannel):
        gw = get_gateway(channel)
        self.channel = channel

        func = gw.get("func")
        if not callable(func):
            raise RuntimeError(
                f"Gateway func not callable for {channel.name}: {func!r}"
            )

        self._exec_func = func
        self._terminal_path = gw.get("terminal_path")

    # ────────────────────────────────
    # Properties
    # ────────────────────────────────

    @property
    def terminal_path(self) -> str | None:
        """Returns the underlying terminal path for diagnostics."""
        return self._terminal_path

    # ────────────────────────────────
    # Core Execution Operations
    # ────────────────────────────────

    def send_order(self, request: OrderRequest) -> ExecutionResult:
        """Send an order to the MetaTrader5 terminal."""
        from MetaTrader5 import order_send  # lazy import

        result = self._exec_func(
            "order_send", order_send, request, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def check_order(self, request: CheckRequest) -> ExecutionResult:
        """Validate an order via MT5 (pre-trade)."""
        from MetaTrader5 import order_check

        result = self._exec_func(
            "order_check", order_check, request, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def get_positions(self, request: QueryRequest | None = None) -> ExecutionResult:
        """Fetch current open positions."""
        from MetaTrader5 import positions_get

        symbol = request.symbol if request else None
        result = self._exec_func(
            "positions_get", positions_get, symbol=symbol, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def get_orders(self, request: QueryRequest | None = None) -> ExecutionResult:
        """Fetch current pending orders."""
        from MetaTrader5 import orders_get

        symbol = request.symbol if request else None
        result = self._exec_func(
            "orders_get", orders_get, symbol=symbol, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result
