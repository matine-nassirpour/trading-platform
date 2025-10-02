from typing import Any, ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class ReconciliationEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.reconciliation"
    app: App = App.PYTHON_CORE
    as_of_ms: int
    diffs: dict[str, Any]  # ex: {"positions":[...], "orders":[...], "deals":[...]}
    status: Literal["match", "mismatch"]
