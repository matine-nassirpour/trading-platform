from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.risk.sl_tp_change_reason import (
    SlTpChangeReason,
)


@dataclass(frozen=True)
class SlTpConfigurationChangedEvent(BaseEvent):
    """
    Canonical event emitted whenever SL and/or TP configuration changes.

    This event is the SINGLE source of truth for:
    - initial SL/TP definition
    - manual updates
    - trailing stop movements
    - breakeven adjustments
    - risk-driven overrides
    """

    event_name: ClassVar[str] = "trading.sl_tp_configuration_changed"
    event_version: ClassVar[int] = 1

    symbol: Symbol

    position_id: PositionId | None
    intent_id: IntentId | None

    old_sl: Price | None
    new_sl: Price | None

    old_tp: Price | None
    new_tp: Price | None

    reason: SlTpChangeReason
