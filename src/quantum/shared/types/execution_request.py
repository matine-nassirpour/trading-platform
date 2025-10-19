from pydantic import BaseModel, ConfigDict

from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import (
    OrderFillingType,
    OrderType,
    TimeInForce,
    TradeAction,
)
from quantum.shared.types.value_objects import Symbol


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


class CheckRequest(BaseModel):
    """Request to check an order's validity before execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: Symbol
    volume: PositiveDecimal
    type: OrderType
    price: PositiveDecimal | None = None
    stop_price: PositiveDecimal | None = None
    limit_price: PositiveDecimal | None = None


class QueryRequest(BaseModel):
    """Request to query orders or positions (optionally filtered)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: Symbol | None = None
