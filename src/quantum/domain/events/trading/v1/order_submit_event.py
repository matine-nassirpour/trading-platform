from typing import ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.domain.serialization import register_event
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs, IntentId, Symbol


@register_event
class OrderSubmitEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_submit"
    app: App = App.EA_MQL5
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs | None = None  # completed in the ACK
    request: dict  # snapshot of the MqlTradeRequest

    @field_validator("response_epoch_ms")
    @classmethod
    def _resp_after_req(cls, v, info):
        req = info.data.get("request_epoch_ms")
        if v is not None and req is not None and v < req:
            raise ValueError("response_epoch_ms must be >= request_epoch_ms")
        return v
