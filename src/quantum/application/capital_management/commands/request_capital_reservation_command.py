from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class RequestCapitalReservationCommand(BaseCommand):
    """Command: request a new capital reservation for a trading decision."""

    reservation_id: CapitalReservationId
    decision_id: DecisionId
    strategy_id: StrategyId
    requested_allocation: CapitalAllocationIntent
