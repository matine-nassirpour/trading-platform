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

from enum import StrEnum, auto


class ExecutionCode(StrEnum):
    # ─── Success
    OK = auto()  # Generic success

    # ─── Generic Failures
    FAIL = auto()  # Generic error
    INVALID_PARAMS = auto()  # Invalid parameters passed
    NO_MEMORY = auto()  # Memory allocation failed
    NOT_FOUND = auto()  # Requested resource not found
    INVALID_VERSION = auto()  # API version mismatch
    AUTH_FAILED = auto()  # Login or credential failure
    UNSUPPORTED = auto()  # Feature not supported
    AUTO_TRADING_DISABLED = auto()  # Auto trading disabled in terminal

    # ─── Internal Infrastructure Failures
    INTERNAL_FAIL = auto()  # Unspecified internal error
    INTERNAL_FAIL_SEND = auto()  # Internal send error
    INTERNAL_FAIL_RECEIVE = auto()  # Internal receive error
    INTERNAL_FAIL_INIT = auto()  # Initialization error
    INTERNAL_FAIL_CONNECT = auto()  # Connection error
    INTERNAL_FAIL_TIMEOUT = auto()  # Timeout (network or process)

    # ─── Trade Retcodes (subset of MT5 TRADE_RETCODE_*)
    TRADE_TIMEOUT = auto()  # Timeout waiting for response
    INVALID_PRICE = auto()  # Invalid price in request
    MARKET_CLOSED = auto()  # Market closed, trading not allowed
    NO_CONNECTION = auto()  # No network or broker connection
    NOT_ENOUGH_MONEY = auto()  # Insufficient margin or balance
    TRADE_DISABLED = auto()  # Trading disabled by broker or symbol
    INVALID_VOLUME = auto()  # Invalid lot size or volume
    INVALID_STOPS = auto()  # Invalid SL/TP configuration
    INVALID_TRADE_PARAMETERS = auto()  # Invalid order parameters
    SERVER_BUSY = auto()  # Broker server overloaded
    BROKER_REJECT = auto()  # Rejected by broker or dealing desk
    POSITION_CLOSED = auto()  # Position no longer active

    # ─── Generic catch-all
    UNKNOWN = auto()  # Unknown or unmapped execution result


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
