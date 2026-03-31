from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.close_position_command import (
    ClosePositionCommand,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.execution.position.aggregate import Position


class ClosePositionHandler(
    AggregateCommandHandler[ClosePositionCommand, None, Position]
):
    """
    Closes an existing Position aggregate.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: ClosePositionCommand) -> str:
        return f"position-{command.position_id.value}"

    def _execute_domain(
        self,
        *,
        command: ClosePositionCommand,
        aggregate: Position | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is None:
            raise RuntimeError(
                "Position aggregate missing despite MUST_EXIST policy enforcement."
            )

        domain_events = aggregate.close(
            exit_price=command.exit_price,
            context=command.context,
        )

        return domain_events, None
