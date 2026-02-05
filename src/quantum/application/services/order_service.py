from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.order_repository import OrderRepository
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill


class OrderService:

    def __init__(
        self,
        repository: OrderRepository,
        event_store: EventStore,
    ) -> None:
        self._repository = repository
        self._event_store = event_store

    def register_fill(self, order_id, fill: ExecutionFill) -> None:
        order = self._repository.load(order_id)

        events = order.register_fill(fill=fill)

        self._event_store.append(events)

    def cancel(self, order_id) -> None:
        order = self._repository.load(order_id)

        events = order.cancel()

        self._event_store.append(events)
