from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class OrderAckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_ack"
    event_version: ClassVar[int] = 1
    intent_id: IntentId
    order_id: OrderId
    symbol: Symbol
    ack_epoch_ms: EpochMs
    app: App = App.EA_MQL5
