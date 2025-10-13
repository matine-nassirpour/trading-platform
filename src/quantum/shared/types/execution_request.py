from pydantic import BaseModel, ConfigDict, Field, field_validator

from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import OrderType, Side, TimeInForce
from quantum.shared.types.ids import Symbol
from quantum.shared.types.symbol import normalize_symbol


class OrderRequest(BaseModel):
    """Canonical order request sent to an execution port."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: Symbol = Field(..., description="Trading symbol, normalized (e.g., EURUSD)")
    side: Side
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

    @field_validator("symbol")
    @classmethod
    def _normalize_symbol(cls, v: Symbol) -> Symbol:
        """Normalize and sanitize the trading symbol."""
        return Symbol(normalize_symbol(v))

    @field_validator("price", "stop_price", "limit_price")
    @classmethod
    def _price_matrix(cls, v, info):
        """Ensure coherence between price fields based on order type."""
        typ: OrderType | None = info.data.get("type")

        if typ == OrderType.MARKET:
            if any(
                info.data.get(k) is not None
                for k in ("price", "stop_price", "limit_price")
            ):
                raise ValueError("MARKET must not define price/stop_price/limit_price")
        elif typ == OrderType.LIMIT:
            if info.data.get("price") is None:
                raise ValueError("LIMIT requires price")
        elif typ == OrderType.STOP:
            if info.data.get("stop_price") is None:
                raise ValueError("STOP requires stop_price")
        elif typ == OrderType.STOP_LIMIT:
            if (
                info.data.get("stop_price") is None
                or info.data.get("limit_price") is None
            ):
                raise ValueError("STOP_LIMIT requires stop_price and limit_price")
        return v


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
