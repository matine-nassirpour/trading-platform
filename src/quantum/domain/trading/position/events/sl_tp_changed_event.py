from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.protection.sl_tp_change_reason import SlTpChangeReason


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

    broker_position_ref: BrokerPositionRef | None
    intent_id: DecisionId | None

    old_sl: Price | None
    new_sl: Price | None

    old_tp: Price | None
    new_tp: Price | None

    reason: SlTpChangeReason
