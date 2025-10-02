from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.typing.time import EpochMs


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
