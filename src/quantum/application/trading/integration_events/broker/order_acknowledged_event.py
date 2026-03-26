from dataclasses import dataclass
from typing import ClassVar

from quantum.application.trading.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId


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
    broker_order_id: BrokerOrderId
    symbol: Symbol
