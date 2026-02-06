from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.repositories.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)


class TradingIntentService:

    def __init__(
        self,
        repository: TradingIntentRepository,
        event_store: EventStore,
    ) -> None:
        self._repository = repository
        self._event_store = event_store

    def authorize(self, intent_id, result: DecisionPolicyResult) -> None:
        intent = self._repository.load(intent_id)

        events = intent.authorize(result=result)

        self._event_store.append(events)

    def reject(self, intent_id, result: DecisionPolicyResult) -> None:
        intent = self._repository.load(intent_id)

        events = intent.reject(result=result)

        self._event_store.append(events)
