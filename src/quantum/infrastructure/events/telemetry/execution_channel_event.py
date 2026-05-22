from typing import ClassVar

from quantum.domain.shared_kernel.event_sourcing.events import BaseEvent
from quantum.domain.trading.common.value_objects import EpochMs
from quantum.infrastructure.execution.contracts.execution_code import ExecutionCode
from quantum.infrastructure.execution.type.execution_channel import ExecutionChannel


class ExecutionChannelEvent(BaseEvent):
    """
    Status of a call to the execution channel (local API → terminal/broker).
    Covers pre-trade successes and failures (before TRADE_RETCODE).
    """

    event_name: ClassVar[str] = "system.execution_channel"
    channel: ExecutionChannel
    code: ExecutionCode
    detail: str | None = None  # message returned by the API
    call: str  # ex: "order_send", "order_check", "initialize", ...
    start_epoch_ms: EpochMs
    end_epoch_ms: EpochMs | None = None
