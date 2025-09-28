from typing import Any, Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class OrderCheckV1(BaseEvent):
    event_name: Literal["order_check_v1"] = "order_check_v1"
    app: Literal["ea_mql5"]
    intent_id: str
    client_order_id: str
    symbol: str
    request_ms: int  # t_send OrderCheck (unix ms)
    response_ms: int | None  # t_resp
    result_code: int  # RETCODE_*
    result_desc: str
    details: dict[str, Any] | None = None  # sl, tp, etc.
