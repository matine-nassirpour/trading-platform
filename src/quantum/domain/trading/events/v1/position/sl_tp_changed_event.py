from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base.fact_event import FactEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.safety.sl_tp_change_reason import SlTpChangeReason
from quantum.domain.trading.identifiers.position_id import PositionId


@dataclass(frozen=True, slots=True)
class SlTpChangedEvent(FactEvent):
    """
    Canonical event emitted whenever SL and/or TP configuration changes.

    This event is the SINGLE source of truth for:
    - initial SL/TP definition
    - manual updates
    - trailing stop movements
    - breakeven adjustments
    - risk-driven overrides
    """

    event_name: ClassVar[str] = "trading.position.sl_tp.changed"
    event_version: ClassVar[int] = 1

    symbol: Symbol

    position_id: PositionId | None
    intent_id: IntentId | None

    old_sl: Price | None
    new_sl: Price | None

    old_tp: Price | None
    new_tp: Price | None

    reason: SlTpChangeReason
