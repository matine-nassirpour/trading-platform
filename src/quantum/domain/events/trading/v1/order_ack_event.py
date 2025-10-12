from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.types.time import EpochMs


class OrderAckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_ack"
    app: App = App.EA_MQL5
    intent_id: str
    client_order_id: str
    order_id: int | None = None
    symbol: str
    ack_epoch_ms: EpochMs
