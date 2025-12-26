from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs, IntentId, Symbol


class OrderRejectEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_reject"
    app: App = App.EA_MQL5
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    reject_epoch_ms: EpochMs
    error_code: int  # RETCODE_*
    error_desc: str
    request_snapshot: dict[str, Any] | None = None
