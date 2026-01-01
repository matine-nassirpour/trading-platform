from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.market.price import Price


@dataclass(frozen=True)
class TrailingTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.trailing_trigger"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    position_id: PositionId

    symbol: Symbol
    new_sl: Price

    trigger_epoch_ms: EpochMs
    price_at_trigger: Price
