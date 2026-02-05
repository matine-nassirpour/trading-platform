from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.position_repository import PositionRepository
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.value_objects.price import Price


class PositionService:

    def __init__(
        self,
        repository: PositionRepository,
        event_store: EventStore,
    ) -> None:
        self._repository = repository
        self._event_store = event_store

    def close(self, position_id, exit_price: Price, context: MoneyContext) -> None:
        position = self._repository.load(position_id)

        events = position.close(exit_price=exit_price, context=context)

        self._event_store.append(events)
