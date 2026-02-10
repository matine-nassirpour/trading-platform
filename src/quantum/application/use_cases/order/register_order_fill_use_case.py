from quantum.application.errors.application_error import NotFoundError
from quantum.application.ports.outbound.repositories.order_repository import (
    OrderRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_processing_service import EventProcessingService
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId


class RegisterOrderFillUseCase:

    def __init__(
        self,
        *,
        order_repository: OrderRepository,
        event_processing: EventProcessingService,
        uow: UnitOfWork,
    ) -> None:
        self._order_repository = order_repository
        self._event_processing = event_processing
        self._uow = uow

    def execute(self, order_id, fill) -> None:

        with self._uow:

            order = self._order_repository.load(order_id)

            if order is None:
                raise NotFoundError(f"No Order found with id: {order_id}")

            domain_events = order.register_fill(fill=fill)

            self._event_processing.process(
                events=domain_events,
                actor=ActorId("system:execution"),
                correlation=CorrelationId.new(),
                causation=CausationId.root(),
            )

            self._uow.commit()
