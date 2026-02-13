from collections.abc import Iterable
from typing import Final

from quantum.application.commands.trading.close_position_command import (
    ClosePositionCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
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

    def _stream_id(self, command: ClosePositionCommand) -> str:
        return f"position-{command.position_id.value}"

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
