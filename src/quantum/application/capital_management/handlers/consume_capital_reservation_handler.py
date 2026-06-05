from collections.abc import Sequence

from quantum.application.capital_management.commands.consume_capital_reservation_command import (
    ConsumeCapitalReservationCommand,
)
from quantum.application.capital_management.results.capital_reservation_command_result import (
    ConsumeCapitalReservationResult,
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


class ConsumeCapitalReservationHandler(
    AggregateCommandHandler[
        ConsumeCapitalReservationCommand,
        ConsumeCapitalReservationResult,
        CapitalReservationId,
        CapitalReservationStateBase,
        CapitalReservation,
    ]
):
    """
    Use case: consume previously reserved capital.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self, command: ConsumeCapitalReservationCommand
    ) -> CapitalReservationId:
        return command.reservation_id

    def _context(
        self, command: ConsumeCapitalReservationCommand
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: ConsumeCapitalReservationCommand,
        aggregate: CapitalReservation,
    ) -> tuple[Sequence[BaseEvent], ConsumeCapitalReservationResult]:
        events = aggregate.consume()

        return events, ConsumeCapitalReservationResult(
            reservation_id=command.reservation_id
        )
