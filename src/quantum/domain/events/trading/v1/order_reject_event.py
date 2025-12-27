from dataclasses import dataclass
from typing import Any, ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class OrderRejectEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_reject"
    intent_id: IntentId
    client_order_id: str
    symbol: Symbol
    reject_epoch_ms: EpochMs
    error_code: int  # RETCODE_*
    error_desc: str
    request_snapshot: dict[str, Any] | None = None
    app: App = App.EA_MQL5
