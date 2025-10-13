from __future__ import annotations

from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import App, DealEntry, DealReason
from quantum.shared.types.ids import DealId, IntentId, OrderId, PositionId, Symbol
from quantum.shared.types.time import EpochMs


@register_event
class TakeProfitTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.takeprofit_trigger"
    app: App = App.EA_MQL5

    intent_id: IntentId | None = None
    order_id: OrderId | None = None
    deal_id: DealId
    position_id: PositionId
    symbol: Symbol

    trigger_price: PositiveDecimal
    tp_price: PositiveDecimal
    volume_closed: PositiveDecimal
    deal_entry: DealEntry = DealEntry.OUT
    reason: DealReason = DealReason.TP
    trigger_epoch_ms: EpochMs
