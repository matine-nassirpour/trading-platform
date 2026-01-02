from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.execution.types.deal_entry import DealEntry
from quantum.domain.execution.types.deal_reason import DealReason
from quantum.domain.execution.value_objects.deal_id import DealId
from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.market.price import Price
from quantum.domain.trading.value_objects.market.volume import PositiveVolume


@dataclass(frozen=True)
class StopLossTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.stoploss_trigger"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Price
    sl_price: Price
    volume_closed: PositiveVolume

    trigger_epoch_ms: EpochMs
    deal_entry: DealEntry = DealEntry.is_out
    reason: DealReason = DealReason.SL
