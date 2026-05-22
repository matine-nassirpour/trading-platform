from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.open_position_command import (
    OpenPositionCommand,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.position.aggregate import Position


class OpenPositionHandler(AggregateCommandHandler[OpenPositionCommand, None, Position]):
    """
    Opens a new Position aggregate.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_NOT_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: OpenPositionCommand) -> str:
        return f"position-{command.position_id.value}"

    def _execute_domain(
        self,
        *,
        command: OpenPositionCommand,
        aggregate: Position | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is not None:
            raise RuntimeError(
                "Position aggregate already exists "
                "despite MUST_NOT_EXIST policy enforcement."
            )

        domain_events = Position.open(
            position_id=command.position_id,
            side=command.side,
            volume=command.volume,
            entry_price=command.entry_price,
        )

        return domain_events, None
