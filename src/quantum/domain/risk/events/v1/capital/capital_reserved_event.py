from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.aggregate import CapitalReservationId
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalReservedEvent(RiskEvent):
    """
    Reservation request has been accepted, and capital is now reserved.

    The reserved allocation MAY differ from the requested allocation.
    """

    event_name: ClassVar[str] = "risk.capital.reserved"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    intent_id: IntentId
    strategy_id: StrategyId
    reserved_allocation: CapitalAllocationIntent
