from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs


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
