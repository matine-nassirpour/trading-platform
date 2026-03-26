from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.value_objects import PositiveVolume, Price
from quantum.infrastructure.execution.type.order_filling_type import OrderFillingType
from quantum.infrastructure.execution.type.trade_action import TradeAction


class OrderRequest(BaseModel):
    """
    Canonical order request sent to an execution port.
    This model defines all parameters required to perform a trading action.
    """

    action: TradeAction
    symbol: Symbol
    volume: PositiveVolume
    type: OrderType
    price: Price | None = Field(None)
    stop_loss: Price | None = Field(None)
    take_profit: Price | None = Field(None)
    deviation: int | None = Field(None)
    time_in_force: TimeInForce = TimeInForce("gtc")
    filling: OrderFillingType
    comment: str | None = Field(None)

    model_config = ConfigDict(extra="forbid", frozen=True)


class CheckRequest(BaseModel):
    """Request to check an order's validity before execution."""

    order: OrderRequest
    stop_price: Price | None = Field(None)
    limit_price: Price | None = Field(None)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @property
    def symbol(self) -> Symbol:
        """Shortcut access to the symbol for convenience."""
        return self.order.symbol

    @property
    def volume(self) -> PositiveVolume:
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
