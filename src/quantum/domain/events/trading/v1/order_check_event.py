from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App
from quantum.domain.types.order_check_outcome import OrderCheckOutcome


@dataclass(frozen=True)
class OrderCheckEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_check"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs

    outcome: OrderCheckOutcome
    reason: str | None = None

    app: App = App.EA_MQL5
