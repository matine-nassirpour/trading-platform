from pydantic import BaseModel, ConfigDict

from quantum.domain.types.decimal_validators import PositiveDecimal
from quantum.domain.types.enums import (
    OrderFillingType,
    OrderType,
    TimeInForce,
    TradeAction,
)
from quantum.domain.value_objects import Symbol


class OrderRequest(BaseModel):
    """Canonical order request sent to an execution port."""

    action: TradeAction
    symbol: Symbol
    volume: PositiveDecimal
    type: OrderType
    price: PositiveDecimal | None
    stop_loss: PositiveDecimal | None
    take_profit: PositiveDecimal | None
    deviation: int | None
    time_in_force: TimeInForce = TimeInForce.GTC
    filling: OrderFillingType
    comment: str | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class CheckRequest(OrderRequest):
    """Request to check an order's validity before execution."""

    symbol: Symbol
    volume: PositiveDecimal
    type: OrderType
    price: PositiveDecimal | None = None
    stop_price: PositiveDecimal | None = None
    limit_price: PositiveDecimal | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class QueryRequest(BaseModel):
    """Request to query orders or positions (optionally filtered)."""

    symbol: Symbol | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)
