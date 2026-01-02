from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.trading.context.market_regime import MarketRegime


@dataclass(frozen=True)
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
