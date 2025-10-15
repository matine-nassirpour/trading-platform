"""
MetaTrader5 Retcode → Internal ExecutionCode Mapping
──────────────────────────────────────────────────────────────────────────────
This module provides a stable and maintainable mapping between
MetaTrader5's `retcode` values and the internal `ExecutionCode` enum.

Responsibilities:
  - Decouple MT5-specific codes from the internal domain language
  - Provide forward compatibility (safe fallback for unknown codes)
  - Support detailed observability and diagnostics
  - Facilitate multi-broker extensibility (MT5, FIX, REST)

This mapping layer is intentionally isolated so that infrastructure code
(mt5_gateway.py, adapters, etc.) remains clean and domain-agnostic.
"""

import logging

from quantum.shared.types.execution import ExecutionCode

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Canonical mapping
# ──────────────────────────────────────────────────────────────────────────────

MT5_RES_TO_EXEC: dict[int, ExecutionCode] = {
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


# ──────────────────────────────────────────────────────────────────────────────
# Mapping function with graceful degradation
# ──────────────────────────────────────────────────────────────────────────────


def map_mt5_res_to_exec(code: int) -> ExecutionCode:
    """
    Maps an MT5 retcode to the internal ExecutionCode enum.

    Returns:
        - The corresponding ExecutionCode if known
        - ExecutionCode.UNKNOWN for unmapped codes (graceful degradation)

    Side effects:
        Logs a warning once per unknown code, aiding in observability
        and future schema enrichment.
    """
    try:
        if code in MT5_RES_TO_EXEC:
            return MT5_RES_TO_EXEC[code]

        logger.warning(
            "Unknown MT5 retcode encountered",
            extra={"attrs": {"retcode": code}},
        )
        return ExecutionCode.UNKNOWN

    except Exception as e:
        logger.exception(f"Error mapping MT5 retcode {code}: {e}")
        return ExecutionCode.INTERNAL_FAIL
