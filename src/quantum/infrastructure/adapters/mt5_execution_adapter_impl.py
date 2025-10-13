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
        self._exec_func = gw["func"]
        self._terminal_path = gw["terminal_path"]

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

    # Core Execution Operations
    def send_order(self, request: OrderRequest) -> ExecutionResult:
        """
        Sends an order to the MetaTrader5 terminal.

        Parameters
        ----------
        request : OrderRequest
            Structured request representing an MQL5 `MqlTradeRequest`.

        Returns
        -------
        ExecutionResult
            Encapsulates the execution code, human-readable message, and raw MT5 payload.
        """
        from MetaTrader5 import order_send  # lazy import

        return self._exec_func("order_send", order_send, request, channel=self.channel)

    def check_order(self, request: CheckRequest) -> ExecutionResult:
        """
        Performs a pre-trade order check via MT5 to validate the order
        without sending it to the market.
        """
        from MetaTrader5 import order_check

        return self._exec_func(
            "order_check", order_check, request, channel=self.channel
        )

    def get_positions(self, request: QueryRequest | None = None) -> ExecutionResult:
        """
        Fetches current open positions for the given symbol.

        Parameters
        ----------
        request : QueryRequest | None
            Optional symbol filter.

        Returns
        -------
        ExecutionResult
        """
        from MetaTrader5 import positions_get

        symbol = request.symbol if request else None
        return self._exec_func(
            "positions_get", positions_get, symbol=symbol, channel=self.channel
        )

    def get_orders(self, request: QueryRequest | None = None) -> ExecutionResult:
        """
        Fetches current pending orders for the given symbol.

        Parameters
        ----------
        request : QueryRequest | None
            Optional symbol filter.

        Returns
        -------
        ExecutionResult
        """
        from MetaTrader5 import orders_get

        symbol = request.symbol if request else None
        return self._exec_func(
            "orders_get", orders_get, symbol=symbol, channel=self.channel
        )
