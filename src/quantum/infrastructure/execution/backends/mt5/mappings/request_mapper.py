"""
MetaTrader5 Request Mapper
──────────────────────────────────────────────────────────────────────────────
Transforms domain-level OrderRequest, CheckRequest, QueryRequest models
into MetaTrader5-compatible `TradeRequest` dictionaries.

Goals
-----
- Strict type and semantic conversion (Enum → int, Decimal → float, etc.)
- Enforce broker-specific field names
- Provide centralized, observable, and testable marshalling
- Facilitate safe extension for multi-broker environments
"""

from __future__ import annotations

import logging

from decimal import Decimal
from typing import Any, Final, cast

from quantum.application.contracts import CheckRequest, OrderRequest, QueryRequest
from quantum.domain.types.enums import (
    OrderFillingType,
    OrderType,
    TimeInForce,
    TradeAction,
)

LOGGER: Final = logging.getLogger(__name__)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Enum & type conversions                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _map_trade_action(action: TradeAction) -> int:
    import MetaTrader5 as mt5  # lazy import for environment portability

    mapping = {
        TradeAction.DEAL: mt5.TRADE_ACTION_DEAL,
        TradeAction.PENDING: mt5.TRADE_ACTION_PENDING,
        TradeAction.SLTP: mt5.TRADE_ACTION_SLTP,
        TradeAction.MODIFY: mt5.TRADE_ACTION_MODIFY,
        TradeAction.REMOVE: mt5.TRADE_ACTION_REMOVE,
        TradeAction.CLOSE_BY: mt5.TRADE_ACTION_CLOSE_BY,
    }

    return cast(int, mapping.get(action, mt5.TRADE_ACTION_DEAL))


def _map_order_type(order_type: OrderType) -> int:
    import MetaTrader5 as mt5

    mapping = {
        OrderType.BUY: mt5.ORDER_TYPE_BUY,
        OrderType.SELL: mt5.ORDER_TYPE_SELL,
        OrderType.BUY_LIMIT: mt5.ORDER_TYPE_BUY_LIMIT,
        OrderType.SELL_LIMIT: mt5.ORDER_TYPE_SELL_LIMIT,
        OrderType.BUY_STOP: mt5.ORDER_TYPE_BUY_STOP,
        OrderType.SELL_STOP: mt5.ORDER_TYPE_SELL_STOP,
        OrderType.BUY_STOP_LIMIT: mt5.ORDER_TYPE_BUY_STOP_LIMIT,
        OrderType.SELL_STOP_LIMIT: mt5.ORDER_TYPE_SELL_STOP_LIMIT,
        OrderType.CLOSE_BY: mt5.ORDER_TYPE_CLOSE_BY,
    }
    return cast(int, mapping.get(order_type, mt5.ORDER_TYPE_BUY))


def _map_time_in_force(tif: TimeInForce) -> int:
    import MetaTrader5 as mt5

    mapping = {
        TimeInForce.GTC: mt5.ORDER_TIME_GTC,
        TimeInForce.DAY: mt5.ORDER_TIME_DAY,
        TimeInForce.SPECIFIED: mt5.ORDER_TIME_SPECIFIED,
        TimeInForce.SPECIFIED_DAY: mt5.ORDER_TIME_SPECIFIED_DAY,
    }
    return cast(int, mapping.get(tif, mt5.ORDER_TIME_GTC))


def _map_type_filling(filling: OrderFillingType) -> int:
    import MetaTrader5 as mt5

    mapping = {
        OrderFillingType.FOK: mt5.ORDER_FILLING_FOK,
        OrderFillingType.IOC: mt5.ORDER_FILLING_IOC,
        OrderFillingType.RETURN: mt5.ORDER_FILLING_RETURN,
    }
    return cast(int, mapping.get(filling, mt5.ORDER_FILLING_FOK))


def _decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Main mappers                                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
def to_mt5_trade_request(req: OrderRequest) -> dict[str, Any]:
    """
    Converts an internal OrderRequest → MT5 TradeRequest dict.
    """
    mt5_dict: dict[str, Any] = {
        "action": _map_trade_action(req.action),
        "symbol": req.symbol.value,
        "volume": float(req.volume),
        "type": _map_order_type(req.type),
        "price": _decimal_to_float(req.price),
        "sl": _decimal_to_float(req.stop_loss),
        "tp": _decimal_to_float(req.take_profit),
        "deviation": int(req.deviation or 10),
        "type_time": _map_time_in_force(req.time_in_force),
        "type_filling": _map_type_filling(req.filling),
    }

    LOGGER.debug(
        "Mapped OrderRequest → MT5 TradeRequest",
        extra={"attrs": {"request": req.model_dump(), "mapped": mt5_dict}},
    )
    return mt5_dict


def to_mt5_check_request(req: CheckRequest) -> dict[str, Any]:
    """
    Converts a CheckRequest → dict suitable for mt5.order_check().
    """
    return to_mt5_trade_request(req)


def to_mt5_query_filter(req: QueryRequest | None) -> dict[str, Any]:
    """
    Converts a QueryRequest to keyword arguments for mt5.orders_get()/positions_get().
    """
    if not req or not req.symbol:
        return {}
    return {"symbol": req.symbol.value}
