from dataclasses import dataclass
from typing import ClassVar

from quantum.application.trading.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class OrderAcknowledgedEvent(IntegrationEvent):
    """
    - The order was received by an external platform.
    - Not yet executed.
    - Not yet accepted economically.
    """

    event_name: ClassVar[str] = "broker.order.acknowledged"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    symbol: Symbol
