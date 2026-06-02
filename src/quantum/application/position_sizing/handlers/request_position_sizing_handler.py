from collections.abc import Sequence

from quantum.application.position_sizing.commands.request_position_sizing_command import (
    RequestPositionSizingCommand,
)
from quantum.application.position_sizing.results.position_sizing_command_result import (
    RequestPositionSizingResult,
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


class RequestPositionSizingHandler(
    AggregateCommandHandler[
        RequestPositionSizingCommand,
        RequestPositionSizingResult,
        PositionSizingId,
        PositionSizingStateBase,
        PositionSizing,
    ]
):
    """
    Use case: request a new position sizing evaluation.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(
        self,
        command: RequestPositionSizingCommand,
    ) -> PositionSizingId:
        return command.sizing_id

    def _context(
        self,
        command: RequestPositionSizingCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: RequestPositionSizingCommand,
        aggregate: PositionSizing,
    ) -> tuple[Sequence[BaseEvent], RequestPositionSizingResult]:
        _, events = PositionSizing.create_new(
            aggregate_id=command.sizing_id,
            decision_id=command.decision_id,
            strategy_id=command.strategy_id,
            symbol=command.symbol,
            allocation=command.allocation,
            equity=command.equity,
            stop_distance=command.stop_distance,
            instrument=command.instrument,
            reference_price=command.reference_price,
            rounding_policy=command.rounding_policy,
        )

        return events, RequestPositionSizingResult(
            sizing_id=command.sizing_id,
        )
