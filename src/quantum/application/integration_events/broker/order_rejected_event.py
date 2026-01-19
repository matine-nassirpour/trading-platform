from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.safety.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True)
class OrderRejectedEvent(IntegrationEvent):
    """
    - Broker rejection
    - Technical rejection
    - Regulatory rejection
    """

    event_name: ClassVar[str] = "trading.order.rejected"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    reject_epoch_ms: EpochMs
    rejection: ExecutionRejection
