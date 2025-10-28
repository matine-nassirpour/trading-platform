from quantum.infrastructure.mt5.adapters.ftmo_adapter import FTMOAdapter
from quantum.infrastructure.mt5.adapters.fundednext_adapter import FUNDEDNEXTAdapter
from quantum.shared.types.channels import ExecutionChannel


def create_adapter(channel: ExecutionChannel):
    if channel == ExecutionChannel.FTMO:
        return FTMOAdapter()
    if channel == ExecutionChannel.FUNDEDNEXT:
        return FUNDEDNEXTAdapter()
    raise ValueError(f"No adapter for channel {channel}")
