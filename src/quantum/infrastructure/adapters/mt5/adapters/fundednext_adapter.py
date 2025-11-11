from quantum.domain.types.execution_channel import ExecutionChannel
from quantum.infrastructure.adapters.mt5.adapters.base_adapter import BaseMt5Adapter


class FUNDEDNEXTAdapter(BaseMt5Adapter):
    def __init__(self) -> None:
        super().__init__(ExecutionChannel.FUNDEDNEXT)
        # (future) apply FTMOExecutionPolicy (slippage, schedules, etc.)
