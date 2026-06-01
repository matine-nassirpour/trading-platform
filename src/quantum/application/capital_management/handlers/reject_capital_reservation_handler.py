from collections.abc import Sequence

from quantum.application.capital_management.commands.reject_capital_reservation_command import (
    RejectCapitalReservationCommand,
)
from quantum.application.capital_management.results.capital_reservation_command_result import (
    RejectCapitalReservationResult,
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


class RejectCapitalReservationHandler(
    AggregateCommandHandler[
        RejectCapitalReservationCommand,
        RejectCapitalReservationResult,
        CapitalReservationId,
        CapitalReservationStateBase,
        CapitalReservation,
    ]
):
    """
    Use case: explicitly reject a pending capital reservation.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self, command: RejectCapitalReservationCommand
    ) -> CapitalReservationId:
        return command.reservation_id

    def _context(
        self, command: RejectCapitalReservationCommand
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: RejectCapitalReservationCommand,
        aggregate: CapitalReservation,
    ) -> tuple[Sequence[BaseEvent], RejectCapitalReservationResult]:
        events = aggregate.reject(reason_code=command.reason_code)

        return events, RejectCapitalReservationResult(
            reservation_id=command.reservation_id,
            reason_code=command.reason_code,
        )
