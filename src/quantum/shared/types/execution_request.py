from pydantic import BaseModel, ConfigDict, Field

from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import OrderType, TimeInForce
from quantum.shared.types.value_objects import Symbol


class OrderRequest(BaseModel):
    """Canonical order request sent to an execution port."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: Symbol = Field(..., description="Trading symbol, normalized (e.g., EURUSD)")
    type: OrderType
    volume: PositiveDecimal = Field(..., description="Lot size")
    price: PositiveDecimal | None = Field(None, description="Price for LIMIT orders")
    stop_price: PositiveDecimal | None = Field(
        None, description="Trigger price for STOP or STOP_LIMIT orders"
    )
    limit_price: PositiveDecimal | None = Field(
        None, description="Execution limit price for STOP_LIMIT orders"
    )
    sl: PositiveDecimal | None = Field(None, description="Stop loss level")
    tp: PositiveDecimal | None = Field(None, description="Take profit level")
    time_in_force: TimeInForce = TimeInForce.GTC
    comment: str | None = None


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
