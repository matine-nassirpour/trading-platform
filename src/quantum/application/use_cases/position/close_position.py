from quantum.application.dto.commands.close_position import ClosePositionCommand
from quantum.application.errors.not_found_errors import PositionNotFound
from quantum.application.ports.outbound.domain_event_publisher import (
    DomainEventPublisher,
)
from quantum.application.ports.outbound.position_repository import PositionRepository
from quantum.application.ports.outbound.unit_of_work import UnitOfWork


class ClosePositionUseCase:
    """
    Closes an open trading position.
    """

    def __init__(
        self,
        *,
        repo: PositionRepository,
        event_publisher: DomainEventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._repo = repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: ClosePositionCommand) -> None:
        with self._uow:
            position = self._repo.get(command.position_id)
            if position is None:
                raise PositionNotFound(command.position_id)

            position = position.close(exit_price=command.exit_price)

            self._repo.save(position)
            self._event_publisher.publish(position.events)
            self._uow.commit()
