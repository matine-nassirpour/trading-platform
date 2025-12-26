from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.decimal_validators import PositiveDecimal
from quantum.domain.types.enums import App


class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    app: App = App.EA_MQL5
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId | None = None
    volume: PositiveDecimal
    price_open: Decimal
    price_current: Decimal
    sl: Decimal | None = None
    tp: Decimal | None = None
    profit: Decimal  # Current PnL (unrealized)
    update_epoch_ms: EpochMs
