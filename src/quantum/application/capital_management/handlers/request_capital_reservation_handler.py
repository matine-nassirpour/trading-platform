from collections.abc import Sequence

from quantum.application.capital_management.commands.request_capital_reservation_command import (
    RequestCapitalReservationCommand,
)
from quantum.application.capital_management.results.capital_reservation_command_result import (
    RequestCapitalReservationResult,
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


class RequestCapitalReservationHandler(
    AggregateCommandHandler[
        RequestCapitalReservationCommand,
        RequestCapitalReservationResult,
        CapitalReservationId,
        CapitalReservationStateBase,
        CapitalReservation,
    ]
):
    """
    Use case: request a new capital reservation.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(
        self, command: RequestCapitalReservationCommand
    ) -> CapitalReservationId:
        return command.reservation_id

    def _context(
        self, command: RequestCapitalReservationCommand
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: RequestCapitalReservationCommand,
        aggregate: CapitalReservation,
    ) -> tuple[Sequence[BaseEvent], RequestCapitalReservationResult]:
        _, events = CapitalReservation.create_new(
            aggregate_id=command.reservation_id,
            decision_id=command.decision_id,
            strategy_id=command.strategy_id,
            requested_allocation=command.requested_allocation,
        )

        return events, RequestCapitalReservationResult(
            reservation_id=command.reservation_id
        )
