from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class OrderAckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_ack"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    symbol: Symbol
    ack_epoch_ms: EpochMs
