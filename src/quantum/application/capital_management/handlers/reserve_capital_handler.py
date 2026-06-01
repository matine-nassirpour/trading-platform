from collections.abc import Sequence

from quantum.application.capital_management.commands.reserve_capital_command import (
    ReserveCapitalCommand,
)
from quantum.application.capital_management.results.capital_reservation_command_result import (
    ReserveCapitalResult,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.capital_management.reservation.aggregate import CapitalReservation
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.capital_management.reservation.events.capital_reservation_rejected_event import (
    CapitalReservationRejectedEvent,
)
from quantum.domain.capital_management.reservation.events.capital_reserved_event import (
    CapitalReservedEvent,
)
from quantum.domain.capital_management.reservation.states.capital_reservation_state_base import (
    CapitalReservationStateBase,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class ReserveCapitalHandler(
    AggregateCommandHandler[
        ReserveCapitalCommand,
        ReserveCapitalResult,
        CapitalReservationId,
        CapitalReservationStateBase,
        CapitalReservation,
    ]
):
    """
    Use case: reserve capital for a pending reservation.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: ReserveCapitalCommand) -> CapitalReservationId:
        return command.reservation_id

    def _context(self, command: ReserveCapitalCommand) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: ReserveCapitalCommand,
        aggregate: CapitalReservation,
    ) -> tuple[Sequence[BaseEvent], ReserveCapitalResult]:
        events = list(
            aggregate.reserve(
                reserved_allocation=command.reserved_allocation,
                budget=command.budget,
            )
        )
        return events, self._build_result(
            reservation_id=command.reservation_id, events=events
        )

    @staticmethod
    def _build_result(
        *,
        reservation_id: CapitalReservationId,
        events: Sequence[BaseEvent],
    ) -> ReserveCapitalResult:
        if len(events) != 1:
            raise RuntimeError(
                "CapitalReservation.reserve() must emit exactly one event"
            )

        event = events[0]

        if isinstance(event, CapitalReservedEvent):
            return ReserveCapitalResult(
                reservation_id=reservation_id,
                accepted=True,
                reserved_allocation=event.reserved_allocation,
                rejection_reason_code=None,
            )

        if isinstance(event, CapitalReservationRejectedEvent):
            return ReserveCapitalResult(
                reservation_id=reservation_id,
                accepted=False,
                reserved_allocation=None,
                rejection_reason_code=event.reason_code,
            )

        raise RuntimeError(f"Unexpected reserve event type: {type(event).__name__}")
