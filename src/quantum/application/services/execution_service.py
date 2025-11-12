import logging

from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.decorators.resilience_injection import bind_resilience
from quantum.application.ports.outbound.execution_port import ExecutionPort
from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort
from quantum.application.resilience.resilience_policy import (
    ResilienceConfig,
    resilient_call,
)
from quantum.application.resilience.retry_policy import RetryPolicy
from quantum.domain.types.execution_channel import ExecutionChannel

logger = logging.getLogger(__name__)


@bind_resilience
class ExecutionService:
    """
    Application service orchestrating execution via an abstract port.
    The domain only knows this service + the port (DIP).
    """

    def __init__(
        self,
        channel: ExecutionChannel,
        port: ExecutionPort,
        *,
        timeout_runner: TimeoutRunnerPort,
        policy: RetryPolicy | None = None,
        cfg: ResilienceConfig | None = None,
    ) -> None:
        self.channel = channel
        self.port = port
        self.timeout_runner = timeout_runner
        self.policy = policy
        self.cfg = cfg

    @resilient_call
    def send_order(self, request: OrderRequest) -> ExecutionResult:
        return self.port.send_order(request)

    @resilient_call
    def check_order(self, request: CheckRequest) -> ExecutionResult:
        return self.port.check_order(request)

    @resilient_call
    def get_positions(self, request: QueryRequest) -> ExecutionResult:
        return self.port.get_positions(request)

    @resilient_call
    def get_orders(self, request: QueryRequest) -> ExecutionResult:
        return self.port.get_orders(request)
