from quantum.domain.types.execution_channel import ExecutionChannel
from quantum.infrastructure.adapters.mt5.adapters.ftmo_adapter import FTMOAdapter
from quantum.infrastructure.adapters.mt5.adapters.fundednext_adapter import (
    FUNDEDNEXTAdapter,
)


def create_adapter(channel: ExecutionChannel):
    if channel == ExecutionChannel.FTMO:
        return FTMOAdapter()
    if channel == ExecutionChannel.FUNDEDNEXT:
        return FUNDEDNEXTAdapter()
    raise ValueError(f"No adapter for channel {channel}")
