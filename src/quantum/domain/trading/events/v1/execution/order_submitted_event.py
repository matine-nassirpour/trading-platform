from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class OrderSubmittedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order.submitted"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
