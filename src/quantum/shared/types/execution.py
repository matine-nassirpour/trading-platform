"""
Canonical execution result codes shared across all trading gateways (MT5, etc.).

These codes are designed to be transport-agnostic and stable across brokers.
They represent logical outcomes, not raw API codes.
"""

from enum import StrEnum


class ExecutionCode(StrEnum):
    OK = "ok"  # RES_S_OK
    FAIL = "fail"  # RES_E_FAIL
    INVALID_PARAMS = "invalid_params"  # RES_E_INVALID_PARAMS
    NO_MEMORY = "no_memory"  # RES_E_NO_MEMORY
    NOT_FOUND = "not_found"  # RES_E_NOT_FOUND
    INVALID_VERSION = "invalid_version"
    AUTH_FAILED = "auth_failed"
    UNSUPPORTED = "unsupported"
    AUTO_TRADING_DISABLED = "auto_trading_disabled"

    # generic group
    INTERNAL_FAIL = "internal_fail"
    INTERNAL_FAIL_SEND = "internal_fail_send"
    INTERNAL_FAIL_RECEIVE = "internal_fail_receive"
    INTERNAL_FAIL_INIT = "internal_fail_init"
    INTERNAL_FAIL_CONNECT = "internal_fail_connect"
    INTERNAL_FAIL_TIMEOUT = "internal_fail_timeout"
