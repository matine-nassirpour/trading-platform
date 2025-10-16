"""
Execution Code Definitions
──────────────────────────────────────────────────────────────────────────────
Canonical enumeration of all normalized execution outcomes
across supported execution backends (MetaTrader5, FIX, REST...).

Each code represents a stable semantic layer decoupled from
vendor-specific return codes (e.g. MT5 `retcode`).

Design goals:
- Provide 1:1 mapping with MT5 retcodes via `mt5_retcode_map.py`
- Be forward-compatible with other backends
- Serve as canonical labels for observability and analytics
"""

from enum import StrEnum


class ExecutionCode(StrEnum):
    # ─── Success
    OK = "ok"  # Generic success

    # ─── Generic Failures
    FAIL = "fail"  # Generic error
    INVALID_PARAMS = "invalid_params"  # Invalid parameters passed
    NO_MEMORY = "no_memory"  # Memory allocation failed
    NOT_FOUND = "not_found"  # Requested resource not found
    INVALID_VERSION = "invalid_version"  # API version mismatch
    AUTH_FAILED = "auth_failed"  # Login or credential failure
    UNSUPPORTED = "unsupported"  # Feature not supported
    AUTO_TRADING_DISABLED = "auto_trading_disabled"  # Auto trading disabled in terminal

    # ─── Internal Infrastructure Failures
    INTERNAL_FAIL = "internal_fail"  # Unspecified internal error
    INTERNAL_FAIL_SEND = "internal_fail_send"  # Internal send error
    INTERNAL_FAIL_RECEIVE = "internal_fail_receive"  # Internal receive error
    INTERNAL_FAIL_INIT = "internal_fail_init"  # Initialization error
    INTERNAL_FAIL_CONNECT = "internal_fail_connect"  # Connection error
    INTERNAL_FAIL_TIMEOUT = "internal_fail_timeout"  # Timeout (network or process)

    # ─── Trade Retcodes (subset of MT5 TRADE_RETCODE_*)
    TRADE_TIMEOUT = "trade_timeout"  # Timeout waiting for response
    INVALID_PRICE = "invalid_price"  # Invalid price in request
    MARKET_CLOSED = "market_closed"  # Market closed, trading not allowed
    NO_CONNECTION = "no_connection"  # No network or broker connection
    NOT_ENOUGH_MONEY = "not_enough_money"  # Insufficient margin or balance
    TRADE_DISABLED = "trade_disabled"  # Trading disabled by broker or symbol
    INVALID_VOLUME = "invalid_volume"  # Invalid lot size or volume
    INVALID_STOPS = "invalid_stops"  # Invalid SL/TP configuration
    INVALID_TRADE_PARAMETERS = "invalid_trade_parameters"  # Invalid order parameters
    SERVER_BUSY = "server_busy"  # Broker server overloaded
    BROKER_REJECT = "broker_reject"  # Rejected by broker or dealing desk
    POSITION_CLOSED = "position_closed"  # Position no longer active

    # ─── Generic catch-all
    UNKNOWN = "unknown"  # Unknown or unmapped execution result


# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────


def is_success(code: "ExecutionCode") -> bool:
    """Returns True if the given code represents a successful execution."""
    return code == ExecutionCode.OK


def is_failure(code: "ExecutionCode") -> bool:
    """Returns True if the given code represents a failure."""
    return code != ExecutionCode.OK


def is_internal_error(code: "ExecutionCode") -> bool:
    """Returns True if the error originated inside the infrastructure."""
    return code.name.startswith("INTERNAL_") or code == ExecutionCode.FAIL


def is_broker_error(code: "ExecutionCode") -> bool:
    """Returns True if the error originates from the broker or trading context."""
    return code.name.startswith("TRADE_") or code in {
        ExecutionCode.MARKET_CLOSED,
        ExecutionCode.NO_CONNECTION,
        ExecutionCode.BROKER_REJECT,
        ExecutionCode.TRADE_DISABLED,
    }
