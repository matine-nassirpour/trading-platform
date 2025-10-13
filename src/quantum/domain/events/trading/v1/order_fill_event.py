from decimal import Decimal
from typing import ClassVar

from pydantic import Field, field_validator

from quantum.domain.events.base import BaseEvent
from quantum.shared.types.decimal_validators import NonNegativeDecimal, PositiveDecimal
from quantum.shared.types.enums import App, DealEntry, DealReason
from quantum.shared.types.time import EpochMs


class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"
    app: App = App.EA_MQL5

    # IDs
    intent_id: str
    order_id: int
    deal_id: int
    symbol: str

    # Current Fill
    price: PositiveDecimal = Field(..., description="Deal price (> 0)")
    volume: PositiveDecimal = Field(
        ..., description="Executed volume on THIS deal (> 0)"
    )
    commission: Decimal
    swap: Decimal
    profit: Decimal

    cum_volume: PositiveDecimal = Field(
        ...,
        description="Cumulative volume executed since order opening, including CE fill",
    )
    leaves_volume: NonNegativeDecimal = Field(
        ..., description="Remaining volume to be executed after CE fill (>= 0)"
    )

    deal_entry: DealEntry
    reason: DealReason
    fill_epoch_ms: EpochMs  # t_fill (unix ms)
    partial: bool

    @field_validator("cum_volume")
    @classmethod
    def _cum_ge_fill(cls, v: Decimal, info):
        """The cumulative cannot be less than the current fill."""
        vol: Decimal | None = info.data.get("volume")
        if vol is not None and v < vol:
            raise ValueError("cum_volume must be >= volume of this fill")
        return v

    @field_validator("leaves_volume")
    @classmethod
    def _leaves_consistency(cls, v: Decimal, info):
        """
        leaves_volume must be >= 0 (guaranteed by NonNegativeDecimal).
        If order_volume is provided, we enforce the following:
        cum_volume + leaves_volume == order_volume
        """
        order_vol: Decimal | None = info.data.get("order_volume")
        cum_v: Decimal | None = info.data.get("cum_volume")
        if order_vol is not None and cum_v is not None:
            # We tolerate a micro-difference due to Decimal rounding depending on your quantization settings.
            if (cum_v + v) != order_vol:
                raise ValueError(
                    "cum_volume + leaves_volume must equal order_volume when order_volume is provided"
                )
        return v
