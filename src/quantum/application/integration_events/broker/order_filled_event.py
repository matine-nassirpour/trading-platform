from dataclasses import dataclass
from typing import ClassVar

from quantum.application.integration_events.base_integration_event import (
    IntegrationEvent,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL
from quantum.domain.shared_kernel.value_objects.swap import Swap
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.deal_id import DealId
from quantum.domain.trading.execution.settlement.fee import Fee
from quantum.domain.trading.execution.taxonomy.deal_entry import DealEntry
from quantum.domain.trading.execution.taxonomy.deal_reason import DealReason
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True)
class OrderFilledEvent(IntegrationEvent):
    event_name: ClassVar[str] = "trading.order.filled"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    order_id: OrderId
    deal_id: DealId
    symbol: Symbol

    price: Price
    volume: PositiveVolume
    commission: Fee
    swap: Swap
    profit: RealizedPnL

    deal_entry: DealEntry
    reason: DealReason
    fill_epoch_ms: EpochMs  # t_fill (unix ms)
    partial: bool
