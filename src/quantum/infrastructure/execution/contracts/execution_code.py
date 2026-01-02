"""
Execution Code Definitions
──────────────────────────
Canonical enumeration of all normalized execution outcomes
across supported execution backends (MetaTrader5, FIX, REST...).

Each code represents a stable semantic layer decoupled from
vendor-specific return codes (e.g. MT5 `retcode`).

Design goals:
- Provide 1:1 mapping with MT5 retcodes via `retcode_map.py`
- Be forward-compatible with other backends
- Serve as canonical labels for observability and analytics
"""

from enum import StrEnum


class ExecutionCode(StrEnum):
    # ─── Success
    OK = "ok"  # Generic success

    # ─── Generic Failures
    FAIL = "fail"
    INVALID_PARAMS = "invalid_params"
    NO_MEMORY = "no_memory"
    NOT_FOUND = "not_found"
    INVALID_VERSION = "invalid_version"
    AUTH_FAILED = "auth_failed"
    UNSUPPORTED = "unsupported"
    AUTO_TRADING_DISABLED = "auto_trading_disabled"

    # ─── Internal Infrastructure Failures
    INTERNAL_FAIL = "internal_fail"
    INTERNAL_FAIL_SEND = "internal_fail_send"
    INTERNAL_FAIL_RECEIVE = "internal_fail_receive"
    INTERNAL_FAIL_INIT = "internal_fail_init"
    INTERNAL_FAIL_CONNECT = "internal_fail_connect"
    INTERNAL_FAIL_TIMEOUT = "internal_fail_timeout"

    # ─── Trade Retcodes (subset of MT5 TRADE_RETCODE_*)
    TRADE_TIMEOUT = "trade_timeout"
    INVALID_PRICE = "invalid_price"
    MARKET_CLOSED = "market_closed"
    NO_CONNECTION = "no_connection"
    NOT_ENOUGH_MONEY = "not_enough_money"
    TRADE_DISABLED = "trade_disabled"
    INVALID_VOLUME = "invalid_volume"
    INVALID_STOPS = "invalid_stops"
    INVALID_TRADE_PARAMETERS = "invalid_trade_parameters"
    SERVER_BUSY = "server_busy"
    BROKER_REJECT = "broker_reject"
    POSITION_CLOSED = "position_closed"

    # ─── Generic catch-all
    UNKNOWN = "unknown"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
