from quantum.application.dto.commands.close_position import ClosePositionCommand
from quantum.application.errors.not_found_errors import PositionNotFound
from quantum.application.ports.aliases import EventPublisher, PositionRepo, UoW


class ClosePositionUseCase:
    """
    Closes an open trading position.
    """

    def __init__(
        self,
        *,
        repo: PositionRepo,
        event_publisher: EventPublisher,
        uow: UoW,
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
