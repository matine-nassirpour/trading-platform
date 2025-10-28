from quantum.infrastructure.adapters.mt5.adapters.base_adapter import BaseMt5Adapter
from quantum.shared.types.channels import ExecutionChannel


class FTMOAdapter(BaseMt5Adapter):
    def __init__(self):
        super().__init__(ExecutionChannel.FTMO)
        # (future) apply FTMOExecutionPolicy (slippage, schedules, etc.)
