from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.market.price import Price
from quantum.domain.trading.value_objects.risk.sl_tp_update_reason import (
    SlTpUpdateReason,
)


@dataclass(frozen=True)
class SlTpUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.sl_tp_update"
    event_version: ClassVar[int] = 1

    symbol: Symbol
    position_id: PositionId
    update_epoch_ms: EpochMs
    reason: SlTpUpdateReason

    intent_id: IntentId | None = None
    old_sl: Price | None = None
    new_sl: Price | None = None
    old_tp: Price | None = None
    new_tp: Price | None = None
