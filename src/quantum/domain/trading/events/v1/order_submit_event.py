from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class OrderSubmitEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_submit"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
