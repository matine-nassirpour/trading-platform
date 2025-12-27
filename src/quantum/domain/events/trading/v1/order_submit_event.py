from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class OrderSubmitEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_submit"
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs | None = None  # completed in the ACK
    app: App = App.EA_MQL5
