from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class OrderCheckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_check"
    app: App = App.EA_MQL5
    intent_id: str
    client_order_id: str
    symbol: str
    request_ms: int  # t_send OrderCheck (unix ms)
    response_ms: int | None = None  # t_resp
    result_code: int  # RETCODE_*
    result_desc: str
    details: dict[str, Any] | None = None  # sl, tp, etc.
