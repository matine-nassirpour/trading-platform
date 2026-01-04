from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.execution.types.order_check_outcome import OrderCheckOutcome
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True)
class OrderCheckEvent(IntegrationEvent):
    event_name: ClassVar[str] = "trading.order_check"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    request_epoch_ms: EpochMs
    response_epoch_ms: EpochMs

    outcome: OrderCheckOutcome
    reason: str | None = None
