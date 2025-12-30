from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import PositiveVolume


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
