from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.repositories.kill_switch_repository import (
    KillSwitchRepository,
)
from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)


class KillSwitchService:

    def __init__(
        self,
        repository: KillSwitchRepository,
        event_store: EventStore,
    ) -> None:
        self._repository = repository
        self._event_store = event_store

    def trigger(self, reason: KillSwitchReason, detail: str | None = None) -> None:
        ks = self._repository.get_current()

        events = ks.trigger(reason=reason, detail=detail)

        self._event_store.append(events)
