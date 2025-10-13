import logging
import time

from quantum.application.ports.outbound.execution_port import ExecutionPort
from quantum.shared.execution.retry_policy import should_retry
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

    def send_order(self, request: OrderRequest) -> ExecutionResult:
        code, msg, result = self.port.send_order(request)
        return ExecutionResult(code=code, message=msg, payload=result)

    def check_order(self, request: CheckRequest) -> ExecutionResult:
        code, msg, result = self.port.check_order(request)
        return ExecutionResult(code=code, message=msg, payload=result)

    def get_positions(self, request: QueryRequest | None = None) -> ExecutionResult:
        code, msg, result = self.port.get_positions(request)
        return ExecutionResult(code=code, message=msg, payload=result)

    def get_orders(self, request: QueryRequest | None = None) -> ExecutionResult:
        code, msg, result = self.port.get_orders(request)
        return ExecutionResult(code=code, message=msg, payload=result)

    # Fault tolerance and retry logic
    def resilient_send(
        self, request: OrderRequest, max_retries: int = 3
    ) -> ExecutionResult:
        """
        Sends an order with automatic retry on transient errors (timeouts, network, etc.)
        and exponential backoff between retries.
        """

        attempt = 0
        last_result: ExecutionResult | None = None

        while attempt < max_retries:
            attempt += 1
            result = self.send_order(request)
            last_result = result

            if not should_retry(result.code):
                return result

            logger.warning(
                f"Retryable MT5 failure ({result.code}), attempt {attempt}/{max_retries}",
                extra={
                    "channel": str(self.channel),
                    "message": result.message,
                },
            )

            # Exponential backoff: 0.5s, 1s, 2s, capped at 5s
            backoff = 0.5 * (2 ** (attempt - 1))
            time.sleep(min(backoff, 5))

        return (
            last_result
            if last_result is not None
            else ExecutionResult.fatal("No response after all retry attempts")
        )
