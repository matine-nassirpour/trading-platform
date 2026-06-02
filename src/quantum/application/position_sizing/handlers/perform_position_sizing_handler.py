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
from quantum.domain.position_sizing.lifecycle.events.position_sized_event import (
    PositionSizedEvent,
)
from quantum.domain.position_sizing.lifecycle.events.position_sizing_rejected_event import (
    PositionSizingRejectedEvent,
)
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

    # --- Internal Helper ------------------------------------------------------

    @staticmethod
    def _build_result(
        *,
        sizing_id: PositionSizingId,
        events: Sequence[BaseEvent],
    ) -> PerformPositionSizingResult:
        if len(events) != 1:
            raise RuntimeError("PositionSizing.size() must emit exactly one event")

        event = events[0]

        if isinstance(event, PositionSizedEvent):
            return PerformPositionSizingResult(
                sizing_id=sizing_id,
                sized=True,
                result=event.result,
                rejection_reason=None,
            )

        if isinstance(event, PositionSizingRejectedEvent):
            return PerformPositionSizingResult(
                sizing_id=sizing_id,
                sized=False,
                result=None,
                rejection_reason=event.reason_code,
            )

        raise RuntimeError(f"Unexpected sizing event type: {type(event).__name__}")

    # --- API ------------------------------------------------------------------

    def _execute_domain(
        self,
        *,
        command: PerformPositionSizingCommand,
        aggregate: PositionSizing,
    ) -> tuple[Sequence[BaseEvent], PerformPositionSizingResult]:
        events = list(aggregate.size())

        result = self._build_result(
            sizing_id=command.sizing_id,
            events=events,
        )

        return events, result
