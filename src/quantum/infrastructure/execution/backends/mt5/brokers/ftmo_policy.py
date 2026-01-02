from quantum.infrastructure.execution.backends.mt5.brokers.base_policy import (
    BrokerPolicy,
)
from quantum.infrastructure.execution.contracts import OrderRequest


class FTMOExecutionPolicy(BrokerPolicy):
    def validate(self, req: OrderRequest) -> None:
        # TODO: implement FTMO rules (examples: news, slippage, min/max volume, etc.)
        return
