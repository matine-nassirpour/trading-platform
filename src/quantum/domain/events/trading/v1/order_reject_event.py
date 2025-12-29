from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.execution_rejection import ExecutionRejection
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class OrderRejectEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_reject"
    event_version: ClassVar[int] = 1
    intent_id: IntentId
    symbol: Symbol
    reject_epoch_ms: EpochMs
    rejection: ExecutionRejection
