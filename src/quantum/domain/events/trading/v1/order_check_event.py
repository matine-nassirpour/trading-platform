from dataclasses import dataclass
from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class OrderCheckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_check"
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    request_epoch_ms: EpochMs
    result_code: int  # RETCODE_*
    result_desc: str
    details: dict[str, Any] | None = None  # sl, tp, etc.
    response_epoch_ms: EpochMs | None = None
    app: App = App.EA_MQL5
