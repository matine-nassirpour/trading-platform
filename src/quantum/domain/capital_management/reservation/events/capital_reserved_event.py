from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.capital_management.events.capital_management_event import (
    CapitalManagementEvent,
)
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalReservedEvent(CapitalManagementEvent):
    """
    Reservation request has been accepted, and capital is now reserved.

    The reserved allocation MAY differ from the requested allocation.
    """

    event_name: ClassVar[str] = "capital_management.capital.reserved"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    decision_id: DecisionId
    strategy_id: StrategyId
    reserved_allocation: CapitalAllocationIntent
