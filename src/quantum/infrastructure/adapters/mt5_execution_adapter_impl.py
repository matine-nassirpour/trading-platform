import logging
import threading
from types import ModuleType

from quantum.infrastructure.execution.contracts import ExecutionFunctionProtocol
from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.execution.mappings.mt5_request_mapper import (
    to_mt5_check_request,
    to_mt5_query_filter,
    to_mt5_trade_request,
)
from quantum.infrastructure.observability.tracing.provider import get_tracer
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.adapters.mt5_exec")

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Lazy import cache for MetaTrader5                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯

_MT5_MODULE: ModuleType | None = None
_MT5_LOCK = threading.Lock()


def _get_mt5_module() -> ModuleType:
    """
    Lazily imports the MetaTrader5 module only once per process.

    Ensures thread safety under concurrent access and prevents
    redundant import overhead during high-frequency execution calls.
    """
    global _MT5_MODULE
    if _MT5_MODULE is None:
        with _MT5_LOCK:
            if _MT5_MODULE is None:
                try:
                    import MetaTrader5 as mt5

                    _MT5_MODULE = mt5
                    logger.info("MetaTrader5 module imported successfully (lazy init).")
                except ImportError as e:
                    logger.critical(
                        "MetaTrader5 package not installed or not importable.",
                        extra={"attrs": {"error": str(e)}},
                    )
                    raise
    return _MT5_MODULE


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Adapter Implementation                                                      │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class Mt5ExecutionAdapterImpl:
    """
    Concrete implementation of the ExecutionPort using the MT5 gateway.

    This adapter bridges the application layer and the MetaTrader5
    infrastructure through a unified and instrumented gateway interface.

    Responsibilities:
    -----------------
    - Delegate calls to MetaTrader5 API via gateway abstraction
    - Enforce consistent ExecutionResult contract
    - Support tracing, metrics, and error handling
    - Optimize import performance with lazy caching
    """

    def __init__(self, channel: ExecutionChannel):
        gw = get_gateway(channel)
        self.channel = channel

        func = gw.func
        if not callable(func):
            raise RuntimeError(
                f"Gateway func not callable for {channel.name}: {func!r}"
            )

        self._exec_func: ExecutionFunctionProtocol = func
        self._terminal_path = gw.terminal_path

    # ─── Properties
    @property
    def terminal_path(self) -> str | None:
        """Return the underlying terminal path for diagnostics."""
        return self._terminal_path

    # ─── Core Execution Operations
    def send_order(self, request: OrderRequest) -> ExecutionResult:
        """Send an order to the MetaTrader5 terminal."""
        mt5 = _get_mt5_module()
        trade_req = to_mt5_trade_request(request)
        result = self._exec_func(
            "order_send", mt5.order_send, trade_req, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def check_order(self, request: CheckRequest) -> ExecutionResult:
        """Validate an order via MT5 (pre-trade)."""
        mt5 = _get_mt5_module()
        trade_req = to_mt5_check_request(request)
        result = self._exec_func(
            "order_check", mt5.order_check, trade_req, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def get_positions(self, request: QueryRequest | None = None) -> ExecutionResult:
        """Fetch current open positions."""
        mt5 = _get_mt5_module()
        filters = to_mt5_query_filter(request)
        result = self._exec_func(
            "positions_get", mt5.positions_get, **filters, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result

    def get_orders(self, request: QueryRequest | None = None) -> ExecutionResult:
        """Fetch current pending orders."""
        mt5 = _get_mt5_module()
        filters = to_mt5_query_filter(request)
        result = self._exec_func(
            "orders_get", mt5.orders_get, **filters, channel=self.channel
        )
        if not isinstance(result, ExecutionResult):
            raise TypeError(f"Expected ExecutionResult, got {type(result)}")
        return result
