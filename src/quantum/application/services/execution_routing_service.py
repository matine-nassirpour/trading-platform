from quantum.application.ports.outbound.broker_gateway import BrokerGateway
from quantum.application.ports.outbound.repositories.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


class ExecutionRoutingService:

    def __init__(
        self,
        intent_repository: TradingIntentRepository,
        gateway: BrokerGateway,
    ) -> None:
        self._intent_repository = intent_repository
        self._gateway = gateway

    def route(self, intent_id: IntentId) -> None:
        intent = self._intent_repository.load(intent_id)

        state = intent.state

        if not state.authorized:
            return

        self._gateway.submit_order(
            symbol=state.context.market_regime,  # exemple symbolique
            order_type=None,
            side=None,
            volume=None,
        )
