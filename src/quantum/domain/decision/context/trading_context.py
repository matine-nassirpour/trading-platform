from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingContext(ValueObject):
    """
    Canonical trading decision context.

    Captures the MARKET STATE under which a decision is made.
    """

    market_regime: MarketRegime

    def _validate(self) -> None:
        if not isinstance(self.market_regime, MarketRegime):
            raise InvariantViolation("TradingContext requires a MarketRegime")

    # --- Canonical factories --------------------------------------------------

    @staticmethod
    def default() -> TradingContext:
        """
        Default context when no special regime is detected.
        """
        return TradingContext(market_regime=MarketRegime.normal())
