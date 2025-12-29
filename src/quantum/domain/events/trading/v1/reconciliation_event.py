from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class ReconciliationEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.reconciliation"
    event_version: ClassVar[int] = 1
    as_of_epoch_ms: EpochMs
    diffs: dict[str, Any]  # ex: {"positions":[...], "orders":[...], "deals":[...]}
    status: Literal["match", "mismatch"]
