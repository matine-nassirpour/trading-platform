from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.execution.value_objects.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True)
class OrderRejectEvent(IntegrationEvent):
    event_name: ClassVar[str] = "trading.order_reject"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    reject_epoch_ms: EpochMs
    rejection: ExecutionRejection
