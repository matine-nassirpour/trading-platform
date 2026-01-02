from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.trading.context.market_regime import MarketRegime


@dataclass(frozen=True)
class MarketRegimeChangedEvent(BaseEvent):
    """
    Emitted when the global market regime changes.

    This event represents a STRUCTURAL change in trading conditions.
    """

    event_name: ClassVar[str] = "trading.market_regime_changed"
    event_version: ClassVar[int] = 1

    previous: MarketRegime
    current: MarketRegime

    trigger_epoch_ms: EpochMs
