from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.market_regime import MarketRegime
from quantum.domain.shared_kernel.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class MarketRegimeChangedEvent(BaseEvent):
    """
    Emitted when the global market regime changes.

    This event represents a STRUCTURAL change in trading conditions.
    """

    event_name: ClassVar[str] = "trading.market_regime.changed"
    event_version: ClassVar[int] = 1

    previous: MarketRegime
    current: MarketRegime
