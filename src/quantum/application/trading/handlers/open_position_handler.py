from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.open_position_command import (
    OpenPositionCommand,
)
from quantum.application.trading.results.position_command_result import (
    OpenPositionResult,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.position.aggregate import Position, PositionId
from quantum.domain.trading.position.states.position_state_base import PositionStateBase


class OpenPositionHandler(
    AggregateCommandHandler[
        OpenPositionCommand,
        OpenPositionResult,
        PositionId,
        PositionStateBase,
        Position,
    ]
):
    """
    Use case: create and open a Position aggregate.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(self, command: OpenPositionCommand) -> PositionId:
        return command.position_id

    def _context(self, command: OpenPositionCommand) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: OpenPositionCommand,
        aggregate: Position,
    ) -> tuple[Sequence[BaseEvent], OpenPositionResult]:
        events = Position.open(
            broker_position_ref=command.broker_position_ref,
            side=command.side,
            volume=command.volume,
            entry_price=command.entry_price,
        )

        return events, OpenPositionResult(position_id=command.position_id)
