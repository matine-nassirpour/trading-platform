from typing import Any, Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class ReconciliationV1(BaseEvent):
    event_name: Literal["reconciliation_v1"] = "reconciliation_v1"
    app: Literal["python_core"]
    as_of_ms: int
    diffs: dict[str, Any]  # ex: {"positions":[...], "orders":[...], "deals":[...]}
    status: Literal["match", "mismatch"]
