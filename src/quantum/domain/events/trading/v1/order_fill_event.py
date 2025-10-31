from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.decimal_validators import NonNegativeDecimal, PositiveDecimal
from quantum.domain.types.enums import App, DealEntry, DealReason
from quantum.domain.value_objects import DealId, EpochMs, IntentId, OrderId, Symbol


class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"
    app: App = App.EA_MQL5

    # IDs
    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    symbol: Symbol

    # Current Fill
    price: PositiveDecimal
    volume: PositiveDecimal
    commission: Decimal
    swap: Decimal
    profit: Decimal

    cum_volume: PositiveDecimal
    leaves_volume: NonNegativeDecimal

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
