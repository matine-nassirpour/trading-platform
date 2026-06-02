from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.close_position_command import (
    ClosePositionCommand,
)
from quantum.application.trading.results.position_command_result import (
    ClosePositionResult,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.position.aggregate import Position, PositionId
from quantum.domain.trading.position.events.position_closed_event import (
    PositionClosedEvent,
)
from quantum.domain.trading.position.states.position_state_base import PositionStateBase


class ClosePositionHandler(
    AggregateCommandHandler[
        ClosePositionCommand,
        ClosePositionResult,
        PositionId,
        PositionStateBase,
        Position,
    ]
):
    """
    Use case: close an opened Position aggregate.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: ClosePositionCommand) -> PositionId:
        return command.position_id

    def _context(self, command: ClosePositionCommand) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: ClosePositionCommand,
        aggregate: Position,
    ) -> tuple[Sequence[BaseEvent], ClosePositionResult]:
        events = list(
            aggregate.close(
                exit_price=command.exit_price,
                instrument=command.instrument,
            )
        )

        realized_pnl = self._extract_realized_pnl(events)

        return events, ClosePositionResult(
            position_id=command.position_id,
            realized_pnl=realized_pnl,
        )

    @staticmethod
    def _extract_realized_pnl(events: Sequence[BaseEvent]):
        if len(events) != 1:
            raise RuntimeError("Position.close() must emit exactly one event")

        event = events[0]

        if not isinstance(event, PositionClosedEvent):
            raise RuntimeError(
                f"Unexpected close position event type: {type(event).__name__}"
            )

        return event.realized_pnl
