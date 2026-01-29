from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.regime.market_regime import MarketRegime
from quantum.domain.shared_kernel.events.base.fact_event import FactEvent


@dataclass(frozen=True, slots=True)
class MarketRegimeChangedEvent(FactEvent):
    """
    Emitted when the global market regime changes.

    This event represents a STRUCTURAL change in trading conditions.
    """

    event_name: ClassVar[str] = "trading.market_regime.changed"
    event_version: ClassVar[int] = 1

    previous: MarketRegime
    current: MarketRegime
