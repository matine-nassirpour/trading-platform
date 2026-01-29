from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.taxonomy.order_check_outcome import (
    OrderCheckOutcome,
)


@dataclass(frozen=True, slots=True)
class OrderCheckedEvent(IntegrationEvent):
    """
    - margin check
    - market open
    - lot size ok
    """

    event_name: ClassVar[str] = "trading.order.checked"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    outcome: OrderCheckOutcome
