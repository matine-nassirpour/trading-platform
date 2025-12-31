from typing import ClassVar

from quantum.application.contracts.execution_code import ExecutionCode
from quantum.domain.model.value_objects import EpochMs
from quantum.domain.shared.events import BaseEvent
from quantum.domain.types.enums import App
from quantum.domain.types.execution_channel import ExecutionChannel


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
