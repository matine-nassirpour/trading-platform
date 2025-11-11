from quantum.application.contracts.execution_request import OrderRequest
from quantum.infrastructure.adapters.mt5.brokers.base_policy import BrokerPolicy


class FUNDEDNEXTExecutionPolicy(BrokerPolicy):
    def validate(self, req: OrderRequest) -> None:
        # TODO: implement FundedNext rules (examples: news, slippage, min/max volume, etc.)
        return
