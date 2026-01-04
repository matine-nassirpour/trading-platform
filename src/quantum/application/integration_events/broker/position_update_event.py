from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.unrealized_pnl import UnrealizedPnL
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


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
    profit: UnrealizedPnL
    update_epoch_ms: EpochMs
    sl: Price | None = None
    tp: Price | None = None
