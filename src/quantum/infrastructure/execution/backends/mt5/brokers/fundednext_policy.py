from quantum.infrastructure.execution.backends.mt5.brokers.base_policy import (
    BrokerPolicy,
)
from quantum.infrastructure.execution.contracts import OrderRequest


class FUNDEDNEXTExecutionPolicy(BrokerPolicy):
    def validate(self, req: OrderRequest) -> None:
        # TODO: implement FundedNext rules (examples: news, slippage, min/max volume, etc.)
        return
