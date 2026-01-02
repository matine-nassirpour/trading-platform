from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.money import Money
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.market.price import Price
from quantum.domain.trading.value_objects.market.volume import PositiveVolume


@dataclass(frozen=True)
class PositionUpdateEvent(IntegrationEvent):
    event_name: ClassVar[str] = "trading.position_update"
    event_version: ClassVar[int] = 1

    symbol: Symbol
    intent_id: IntentId
    volume: PositiveVolume
    price_current: Price
    price_open: Price
    position_id: PositionId
    profit: Money  # Current PnL (unrealized)
    update_epoch_ms: EpochMs
    sl: Price | None = None
    tp: Price | None = None
