from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.time import EpochMs


@register_event
class ExecutionChannelEvent(BaseEvent):
    """
    Status of a call to the execution channel (local API → terminal/broker).
    Covers pre-trade successes and failures (before TRADE_RETCODE).
    """

    event_name: ClassVar[str] = "system.execution_channel"
    app: App = App.PYTHON_CORE
    channel: ExecutionChannel
    code: ExecutionCode
    detail: str | None = None  # message returned by the API
    call: str  # ex: "order_send", "order_check", "initialize", ...
    start_epoch_ms: EpochMs
    end_epoch_ms: EpochMs | None = None
