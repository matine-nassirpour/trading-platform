from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.trading.commands.open_position_command import (
    OpenPositionCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.position.position import Position


class OpenPositionHandler(AggregateCommandHandler[OpenPositionCommand, None, Position]):
    """
    Opens a new Position aggregate.
    """

    def _stream_id(self, command: OpenPositionCommand) -> str:
        return f"position-{command.position_id.value}"

    def _execute_domain(
        self,
        *,
        command: OpenPositionCommand,
        aggregate: Position,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = Position.open(
            position_id=command.position_id,
            side=command.side,
            volume=command.volume,
            entry_price=command.entry_price,
        )

        return domain_events, None
