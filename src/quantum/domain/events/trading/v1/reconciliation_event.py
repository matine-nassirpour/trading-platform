from typing import Any, ClassVar, Literal

from quantum.shared.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App
from quantum.shared.types.value_objects import EpochMs


@register_event
class ReconciliationEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.reconciliation"
    app: App = App.PYTHON_CORE
    as_of_epoch_ms: EpochMs
    diffs: dict[str, Any]  # ex: {"positions":[...], "orders":[...], "deals":[...]}
    status: Literal["match", "mismatch"]
