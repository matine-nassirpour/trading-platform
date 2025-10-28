from quantum.infrastructure.mt5.adapters.base_adapter import BaseMt5Adapter
from quantum.shared.types.channels import ExecutionChannel


class FUNDEDNEXTAdapter(BaseMt5Adapter):
    def __init__(self):
        super().__init__(ExecutionChannel.FUNDEDNEXT)
        # (future) apply FTMOExecutionPolicy (slippage, schedules, etc.)
