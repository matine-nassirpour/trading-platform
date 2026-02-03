from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.safety.execution_rejection import (
    ExecutionRejection,
)


@dataclass(frozen=True, slots=True)
class OrderRejectedEvent(IntegrationEvent):
    """
    - Broker rejection
    - Technical rejection
    - Regulatory rejection
    """

    event_name: ClassVar[str] = "broker.order.rejected"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    rejection: ExecutionRejection
