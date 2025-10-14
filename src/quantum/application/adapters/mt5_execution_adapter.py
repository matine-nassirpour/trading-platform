import logging

from quantum.application.ports.outbound.execution_port import ExecutionPort
from quantum.shared.execution.resilience_policy import resilient_call
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class Mt5ExecutionAdapter:
    """
    Application-level adapter using an injected execution port
    (dependency inversion principle).
    """

    def __init__(self, channel: ExecutionChannel, port: ExecutionPort):
        self.channel = channel
        self.port = port

    @resilient_call("send_order")
    def send_order(self, request: OrderRequest) -> ExecutionResult:
        return self.port.send_order(request)

    @resilient_call("check_order")
    def check_order(self, request: CheckRequest) -> ExecutionResult:
        return self.port.check_order(request)

    @resilient_call("get_positions")
    def get_positions(self, request: QueryRequest | None = None) -> ExecutionResult:
        return self.port.get_positions(request)

    @resilient_call("get_orders")
    def get_orders(self, request: QueryRequest | None = None) -> ExecutionResult:
        return self.port.get_orders(request)
