import logging
from typing import Any

from quantum.application.ports.outbound.execution_port import ExecutionPort
from quantum.shared.execution.retry_policy import should_retry
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode

logger = logging.getLogger(__name__)


class Mt5ExecutionAdapter:
    """
    Application-level adapter using an injected execution port
    (dependency inversion principle).
    """

    def __init__(self, channel: ExecutionChannel, port: ExecutionPort):
        self.channel = channel
        self.port = port

    def send_order(self, request: dict[str, Any]):
        return self.port.send_order(request)

    def check_order(self, request: dict[str, Any]):
        return self.port.check_order(request)

    def get_positions(self, symbol: str | None = None):
        return self.port.get_positions(symbol)

    def get_orders(self, symbol: str | None = None):
        return self.port.get_orders(symbol)

    # Fault tolerance and retry logic
    def resilient_send(
        self, request: dict[str, Any], max_retries: int = 3
    ) -> tuple[ExecutionCode, str, Any | None]:
        """
        Sends an order with automatic retry on transient errors (timeouts, network, etc.).
        """
        code: ExecutionCode = ExecutionCode.INTERNAL_FAIL
        msg: str = ""
        result: Any | None = None

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            code, msg, result = self.send_order(request)
            if not should_retry(code):
                return code, msg, result
            logger.warning(
                f"Retryable MT5 failure ({code}), attempt {attempt}/{max_retries}",
                extra={"channel": str(self.channel), "msg": msg},
            )
        return code, msg, result
