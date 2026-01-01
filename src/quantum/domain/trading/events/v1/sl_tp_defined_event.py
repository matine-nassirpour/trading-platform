from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.market.price import Price


@dataclass(frozen=True)
class SlTpDefinedEvent(BaseEvent):
    """
    Emitted when initial SL / TP are defined for an intent or position.

    Audit meaning:
    - initial risk envelope defined
    """

    event_name: ClassVar[str] = "trading.sl_tp_defined"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    sl: Price | None
    tp: Price | None
    decision_epoch_ms: EpochMs
    rationale: str | None = None
