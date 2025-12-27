from __future__ import annotations

from decimal import Decimal

from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.position_side import PositionSide


class PnLService:
    """
    Canonical domain service for PnL computation.
    Centralizes all PnL logic to avoid divergence.
    """

    @staticmethod
    def compute_realized_pnl(
        entry_price: Price,
        exit_price: Price,
        volume: Volume,
        side: PositionSide,
        currency: str,
    ) -> Money:
        delta = exit_price.value - entry_price.value
        pnl_value = delta * volume.value * Decimal(side.sign())
        return Money(pnl_value, currency)
