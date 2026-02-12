from collections.abc import Iterable
from typing import Final

from quantum.application.commands.trading.close_position_command import (
    ClosePositionCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.application.ports.outbound.repositories.position_repository import (
    PositionRepository,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.position.position import Position


class ClosePositionHandler(
    EventSourcedCommandHandler[ClosePositionCommand, None, Position]
):
    """
    Closes an existing Position aggregate.
    """

    _ACTOR: Final[str] = "system:position"

    def __init__(
        self,
        *,
        position_repository: PositionRepository,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._position_repository = position_repository

    def _stream_id(self, command: ClosePositionCommand) -> str:
        return f"position-{command.position_id.value}"

    def _load_aggregate(self, command: ClosePositionCommand) -> Position:
        return self._position_repository.load(command.position_id)

    def _execute_domain(
        self,
        *,
        command: ClosePositionCommand,
        aggregate: Position,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.close(
            exit_price=command.exit_price,
            context=command.context,
        )

        return domain_events, None
