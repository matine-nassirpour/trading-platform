from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App
from quantum.shared.types.time import EpochMs


@register_event
class OrderRejectEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_reject"
    app: App = App.EA_MQL5
    intent_id: str
    client_order_id: str
    symbol: str
    reject_epoch_ms: EpochMs
    error_code: int  # RETCODE_*
    error_desc: str
    request_snapshot: dict[str, Any] | None = None
