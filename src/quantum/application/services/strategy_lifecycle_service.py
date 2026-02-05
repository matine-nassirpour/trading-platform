from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)
from quantum.domain.trading.events.v1.governance.strategy_lifecycle_changed_event import (
    StrategyLifecycleChangedEvent,
)


class StrategyLifecycleService:

    def __init__(self, event_store: EventStore):
        self._event_store = event_store

    def publish_change(
        self,
        strategy_id: StrategyId,
        previous: StrategyLifecycleState,
        current: StrategyLifecycleState,
    ):

        event = StrategyLifecycleChangedEvent(
            strategy_id=strategy_id,
            previous=previous,
            current=current,
        )

        self._event_store.append([event])
