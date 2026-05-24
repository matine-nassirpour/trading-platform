from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalReservationRequestedEvent(RiskEvent):
    """
    Request to reserve capital for a given TradingIntent.
    """

    event_name: ClassVar[str] = "risk.capital.requested"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    decision_id: DecisionId
    strategy_id: StrategyId
    requested_allocation: CapitalAllocationIntent
