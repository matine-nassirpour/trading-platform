from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers import IntentId, OrderId
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True)
class OrderCreatedEvent(BaseEvent):
    """
    Emitted when an order is created inside a TradingIntent.

    Audit meaning:
    - sizing decision taken
    - exposure intent materialized
    """

    event_name: ClassVar[str] = "trading.order_created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    symbol: Symbol
    volume: PositiveVolume
    decision_epoch_ms: EpochMs
