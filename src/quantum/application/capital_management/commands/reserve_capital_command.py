from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.capital_management.reservation.capital_budget_snapshot import (
    CapitalBudgetSnapshot,
)
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)


@dataclass(frozen=True, slots=True)
class ReserveCapitalCommand(BaseCommand):
    """
    Command: accept a pending capital reservation if budget policy allows it.

    The domain may emit either:
    - CapitalReservedEvent
    - CapitalReservationRejectedEvent
    """

    reservation_id: CapitalReservationId
    reserved_allocation: CapitalAllocationIntent
    budget: CapitalBudgetSnapshot
