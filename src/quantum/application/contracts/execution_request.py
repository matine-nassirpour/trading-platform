from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.model.value_objects import Symbol
from quantum.domain.types.decimal_validators import PositiveDecimal
from quantum.domain.types.enums import (
    OrderFillingType,
    OrderType,
    TimeInForce,
    TradeAction,
)


class OrderRequest(BaseModel):
    """
    Canonical order request sent to an execution port.
    This model defines all parameters required to perform a trading action.
    """

    action: TradeAction
    symbol: Symbol
    volume: PositiveDecimal
    type: OrderType
    price: PositiveDecimal | None = Field(None)
    stop_loss: PositiveDecimal | None = Field(None)
    take_profit: PositiveDecimal | None = Field(None)
    deviation: int | None = Field(None)
    time_in_force: TimeInForce = TimeInForce.GTC
    filling: OrderFillingType
    comment: str | None = Field(None)

    model_config = ConfigDict(extra="forbid", frozen=True)


class CheckRequest(BaseModel):
    """Request to check an order's validity before execution."""

    order: OrderRequest
    stop_price: PositiveDecimal | None = Field(None)
    limit_price: PositiveDecimal | None = Field(None)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @property
    def symbol(self) -> Symbol:
        """Shortcut access to the symbol for convenience."""
        return self.order.symbol

    @property
    def volume(self) -> PositiveDecimal:
        """Shortcut access to the order volume."""
        return self.order.volume

    @property
    def type(self) -> OrderType:
        """Shortcut access to the order type."""
        return self.order.type


class QueryRequest(BaseModel):
    """Request to query orders or positions (optionally filtered)."""

    symbol: Symbol | None = Field(None, description="Filter by symbol if provided")

    model_config = ConfigDict(extra="forbid", frozen=True)
