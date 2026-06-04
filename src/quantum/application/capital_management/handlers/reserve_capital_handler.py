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
        outcome, events = aggregate.reserve(
            reserved_allocation=command.reserved_allocation,
            budget=command.budget,
        )

        return events, ReserveCapitalResult(
            reservation_id=command.reservation_id,
            accepted=outcome.accepted,
            reserved_allocation=outcome.reserved_allocation,
            rejection_reason_code=outcome.rejection_reason_code,
        )
