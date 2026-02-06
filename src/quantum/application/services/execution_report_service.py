from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.repositories.order_repository import (
    OrderRepository,
)
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill


class ExecutionReportService:

    def __init__(
        self,
        order_repository: OrderRepository,
        event_store: EventStore,
    ) -> None:
        self._order_repository = order_repository
        self._event_store = event_store

    def handle_report(
        self,
        *,
        order_id,
        fill: ExecutionFill,
    ) -> None:

        order = self._order_repository.load(order_id)

        events = order.register_fill(fill=fill)

        self._event_store.append(events)
