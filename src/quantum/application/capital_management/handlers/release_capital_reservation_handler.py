from collections.abc import Sequence

from quantum.application.capital_management.commands.release_capital_reservation_command import (
    ReleaseCapitalReservationCommand,
)
from quantum.application.capital_management.results.capital_reservation_command_result import (
    ReleaseCapitalReservationResult,
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


class ReleaseCapitalReservationHandler(
    AggregateCommandHandler[
        ReleaseCapitalReservationCommand,
        ReleaseCapitalReservationResult,
        CapitalReservationId,
        CapitalReservationStateBase,
        CapitalReservation,
    ]
):
    """
    Use case: release previously reserved capital.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self, command: ReleaseCapitalReservationCommand
    ) -> CapitalReservationId:
        return command.reservation_id

    def _context(
        self, command: ReleaseCapitalReservationCommand
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: ReleaseCapitalReservationCommand,
        aggregate: CapitalReservation,
    ) -> tuple[Sequence[BaseEvent], ReleaseCapitalReservationResult]:
        events = aggregate.release(reason_code=command.reason_code)

        return events, ReleaseCapitalReservationResult(
            reservation_id=command.reservation_id
        )
