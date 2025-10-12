import logging
from typing import Any

from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.adapters.mt5_exec")


class Mt5ExecutionAdapterImpl:
    """
    Concrete implementation of the ExecutionPort using the MT5 gateway.
    """

    def __init__(self, channel: ExecutionChannel):
        gw = get_gateway(channel)
        self.channel = channel
        self._exec_func = gw["func"]
        self._terminal_path = gw["terminal_path"]

    @property
    def terminal_path(self) -> str | None:
        return self._terminal_path

    # Core Execution Operations
    def send_order(
        self, request: dict[str, Any]
    ) -> tuple[ExecutionCode, str, Any | None]:
        """
        Sends an order to the MetaTrader5 terminal.

        Parameters
        ----------
        request : dict
            A structured MqlTradeRequest dictionary (as expected by MT5).

        Returns
        -------
        tuple[ExecutionCode, str, Any | None]
            Execution result code, message, and raw MT5 response object.
        """
        from MetaTrader5 import order_send  # lazy import

        return self._exec_func("order_send", order_send, request, channel=self.channel)

    def check_order(
        self, request: dict[str, Any]
    ) -> tuple[ExecutionCode, str, Any | None]:
        """Performs a pre-trade order check via MT5."""
        from MetaTrader5 import order_check

        return self._exec_func(
            "order_check", order_check, request, channel=self.channel
        )

    def get_positions(
        self, symbol: str | None = None
    ) -> tuple[ExecutionCode, str, Any | None]:
        """Fetches current open positions for the given symbol."""
        from MetaTrader5 import positions_get

        return self._exec_func(
            "positions_get", positions_get, symbol=symbol, channel=self.channel
        )

    def get_orders(
        self, symbol: str | None = None
    ) -> tuple[ExecutionCode, str, Any | None]:
        """Fetches current pending orders."""
        from MetaTrader5 import orders_get

        return self._exec_func(
            "orders_get", orders_get, symbol=symbol, channel=self.channel
        )
