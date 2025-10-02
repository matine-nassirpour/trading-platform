from typing import Any, ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.typing.time import EpochMs


class OrderCheckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_check"
    app: App = App.EA_MQL5
    intent_id: str
    client_order_id: str
    symbol: str
    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs | None = None
    result_code: int  # RETCODE_*
    result_desc: str
    details: dict[str, Any] | None = None  # sl, tp, etc.

    @field_validator("response_epoch_ms")
    @classmethod
    def _resp_after_req(cls, v, info):
        req = info.data.get("request_epoch_ms")
        if v is not None and req is not None and v < req:
            raise ValueError("response_epoch_ms must be >= request_epoch_ms")
        return v
