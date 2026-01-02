from quantum.application.dto.commands.cancel_order import CancelOrderCommand
from quantum.application.errors.not_found_errors import OrderNotFound
from quantum.application.ports.outbound.domain_event_publisher import (
    DomainEventPublisher,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork


class CancelOrderUseCase:
    def __init__(
        self, order_repo, event_publisher: DomainEventPublisher, uow: UnitOfWork
    ):
        self._order_repo = order_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: CancelOrderCommand):
        with self._uow:
            order = self._order_repo.get(command.order_id)
            if order is None:
                raise OrderNotFound(command.order_id)

            order = order.cancel()

            self._order_repo.save(order)
            self._event_publisher.publish(order.events)
            self._uow.commit()
