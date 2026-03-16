from dataclasses import dataclass
from typing import ClassVar

from quantum.application.trading.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.deal_id import DealId
from quantum.domain.trading.execution.taxonomy.deal_entry import DealEntry
from quantum.domain.trading.execution.taxonomy.deal_reason import DealReason
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.identifiers.position_id import PositionId


@dataclass(frozen=True, slots=True)
class StopLossTriggeredEvent(IntegrationEvent):
    """
    - triggered by the broker
    - related to execution
    - not business decisions
    """

    event_name: ClassVar[str] = "broker.stoploss.triggered"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    broker_order_id: BrokerOrderId
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Price
    sl_price: Price
    volume_closed: PositiveVolume

    deal_entry: DealEntry
    reason: DealReason
