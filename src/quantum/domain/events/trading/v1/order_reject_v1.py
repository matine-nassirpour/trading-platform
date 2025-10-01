from typing import Any, Literal

from quantum.domain.events.base import BaseEvent


class OrderRejectV1(BaseEvent):
    event_name: Literal["order_reject_v1"] = "order_reject_v1"
    app: Literal["ea_mql5"]
    intent_id: str
    client_order_id: str
    symbol: str
    reject_ms: int
    error_code: int  # RETCODE_*
    error_desc: str
    request_snapshot: dict[str, Any] | None = None
