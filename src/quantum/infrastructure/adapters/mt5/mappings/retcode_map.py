"""
MetaTrader5 Retcode → Internal ExecutionCode Mapping
──────────────────────────────────────────────────────────────────────────────
Provides a clean, thread-safe and observable mapping between
MetaTrader5's `retcode` values and the internal `ExecutionCode` enum.

Design goals
------------
- Decouple MT5-specific codes from the internal domain model
- Guarantee forward-compatibility (graceful fallback for unknown codes)
- Avoid log noise: warn once per unknown retcode
- Preserve observability for metrics, tracing, and diagnostics
"""

from __future__ import annotations

import logging
import threading
from typing import Final

from quantum.application.contracts.execution_code import ExecutionCode

logger = logging.getLogger(__name__)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Canonical mapping                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
MT5_RES_TO_EXEC: Final[dict[int, ExecutionCode]] = {
    # ─── Generic Success
    1: ExecutionCode.OK,
    # ─── Generic Failures
    -1: ExecutionCode.FAIL,
    -2: ExecutionCode.INVALID_PARAMS,
    -3: ExecutionCode.NO_MEMORY,
    -4: ExecutionCode.NOT_FOUND,
    -5: ExecutionCode.INVALID_VERSION,
    -6: ExecutionCode.AUTH_FAILED,
    -7: ExecutionCode.UNSUPPORTED,
    -8: ExecutionCode.AUTO_TRADING_DISABLED,
    # ─── Internal Failures
    -10000: ExecutionCode.INTERNAL_FAIL,
    -10001: ExecutionCode.INTERNAL_FAIL_SEND,
    -10002: ExecutionCode.INTERNAL_FAIL_RECEIVE,
    -10003: ExecutionCode.INTERNAL_FAIL_INIT,
    -10004: ExecutionCode.INTERNAL_FAIL_CONNECT,
    -10005: ExecutionCode.INTERNAL_FAIL_TIMEOUT,
    # ─── Trade Retcodes (subset of TRADE_RETCODE_*)
    10009: ExecutionCode.TRADE_TIMEOUT,
    10006: ExecutionCode.INVALID_PRICE,
    10030: ExecutionCode.MARKET_CLOSED,
    10031: ExecutionCode.NO_CONNECTION,
    10032: ExecutionCode.NOT_ENOUGH_MONEY,
    10033: ExecutionCode.TRADE_DISABLED,
    10034: ExecutionCode.INVALID_VOLUME,
    10035: ExecutionCode.INVALID_STOPS,
    10036: ExecutionCode.INVALID_TRADE_PARAMETERS,
    10037: ExecutionCode.SERVER_BUSY,
    10038: ExecutionCode.BROKER_REJECT,
    10039: ExecutionCode.POSITION_CLOSED,
}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Unknown code tracking (warn-once cache)                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
_UNKNOWN_CODES: set[int] = set()
_UNKNOWN_LOCK = threading.Lock()


def _warn_once_for_unknown(code: int) -> None:
    """
    Emits a warning only the first time a given unknown retcode is seen.
    Thread-safe and idempotent.
    """
    if code in _UNKNOWN_CODES:
        return
    with _UNKNOWN_LOCK:
        if code not in _UNKNOWN_CODES:
            _UNKNOWN_CODES.add(code)
            logger.warning(
                f"Unknown MT5 retcode encountered: {code}",
                extra={"attrs": {"retcode": code}},
            )


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public mapping function                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def map_mt5_res_to_exec(code: int | None) -> ExecutionCode:
    """
    Maps an MT5 retcode to the internal ExecutionCode enum.

    Returns:
        - Known ExecutionCode (exact mapping)
        - ExecutionCode.UNKNOWN if unmapped or None
        - ExecutionCode.INTERNAL_FAIL on unexpected error

    Logging:
        - Warns once per unknown code (never spams logs)
        - Logs exceptions only on mapping failure
    """
    if code is None:
        _warn_once_for_unknown(-9999)
        return ExecutionCode.UNKNOWN

    try:
        exec_code = MT5_RES_TO_EXEC.get(code)
        if exec_code is not None:
            return exec_code

        _warn_once_for_unknown(code)
        return ExecutionCode.UNKNOWN

    except Exception as e:
        logger.exception(f"Error mapping MT5 retcode {code}: {e}")
        return ExecutionCode.INTERNAL_FAIL
