from quantum.application.errors.not_found_errors import PositionNotFound
from quantum.application.ports.outbound.repositories.position_repository import (
    PositionRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_processing_service import EventProcessingService
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId


class ClosePositionUseCase:

    def __init__(
        self,
        *,
        position_repository: PositionRepository,
        event_processing: EventProcessingService,
        uow: UnitOfWork,
    ) -> None:
        self._position_repository = position_repository
        self._event_processing = event_processing
        self._uow = uow

    def execute(self, position_id, exit_price, context):

        with self._uow:

            position = self._position_repository.load(position_id)

            if position is None:
                raise PositionNotFound(position_id)

            domain_events = position.close(
                exit_price=exit_price,
                context=context,
            )

            self._event_processing.process(
                events=domain_events,
                actor=ActorId("system:position"),
                correlation=CorrelationId.new(),
                causation=CausationId.root(),
            )

            self._uow.commit()
