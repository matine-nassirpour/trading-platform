from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.value_objects.currency import Currency
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.value_objects.order.position_side import PositionSide


class PnLService:
    """
    Canonical domain service for PnL computation.

    Responsibilities:
    - Compute realized PnL
    - Enforce sign convention (LONG / SHORT)
    - Remain currency-safe and deterministic
    """

    @staticmethod
    def compute_realized_pnl(
        *,
        entry_price: Price,
        exit_price: Price,
        volume: PositiveVolume,
        side: PositionSide,
        currency: Currency,
    ) -> RealizedPnL:
        """
        Computes realized PnL for a closed position.

        Formula:
            pnl = (exit_price - entry_price) * volume * side_sign
        """

        delta = exit_price.value - entry_price.value
        pnl_value = delta * volume.value * Decimal(side.sign())

        return RealizedPnL(value=pnl_value, currency=currency)
