from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.deal_id import DealId
from quantum.domain.trading.execution.taxonomy.deal_entry import DealEntry
from quantum.domain.trading.execution.taxonomy.deal_reason import DealReason
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


@dataclass(frozen=True)
class TakeProfitTriggeredEvent(IntegrationEvent):
    """
    - triggered by the broker
    - related to execution
    - not business decisions
    """

    event_name: ClassVar[str] = "trading.takeprofit.triggered"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: Price
    tp_price: Price
    volume_closed: PositiveVolume

    trigger_epoch_ms: EpochMs
    deal_entry: DealEntry = DealEntry
    reason: DealReason = DealReason
