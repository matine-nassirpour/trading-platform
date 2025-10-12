from quantum.infrastructure.execution.mt5_gateway import execute_mt5_call
from quantum.shared.types.channels import ExecutionChannel

_GATEWAYS = {
    ExecutionChannel.FUNDEDNEXT: {
        "func": execute_mt5_call,
        "terminal_path": "/path/to/FundedNext/terminal.exe",
    },
    ExecutionChannel.FTMO: {
        "func": execute_mt5_call,
        "terminal_path": "/path/to/FTMO/terminal.exe",
    },
}


def get_gateway(channel: ExecutionChannel):
    """Returns the execution gateway configuration for the given channel."""
    return _GATEWAYS[channel]
