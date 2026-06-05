from collections.abc import Sequence

from quantum.application.position_sizing.commands.perform_position_sizing_command import (
    PerformPositionSizingCommand,
)
from quantum.application.position_sizing.results.position_sizing_command_result import (
    PerformPositionSizingResult,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.position_sizing.aggregate import PositionSizing
from quantum.domain.position_sizing.lifecycle.states.position_sizing_state_base import (
    PositionSizingStateBase,
)
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class PerformPositionSizingHandler(
    AggregateCommandHandler[
        PerformPositionSizingCommand,
        PerformPositionSizingResult,
        PositionSizingId,
        PositionSizingStateBase,
        PositionSizing,
    ]
):
    """
    Use case: perform sizing for a pending PositionSizing aggregate.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: PerformPositionSizingCommand,
    ) -> PositionSizingId:
        return command.sizing_id

    def _context(
        self,
        command: PerformPositionSizingCommand,
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: PerformPositionSizingCommand,
        aggregate: PositionSizing,
    ) -> tuple[Sequence[BaseEvent], PerformPositionSizingResult]:
        outcome, events = aggregate.size()

        return events, PerformPositionSizingResult(
            sizing_id=command.sizing_id,
            sized=outcome.sized,
            result=outcome.result,
            rejection_reason=outcome.rejection_reason,
        )
