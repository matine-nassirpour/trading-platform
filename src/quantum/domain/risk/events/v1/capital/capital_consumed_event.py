from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.capital.reservation.aggregate import CapitalReservationId
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalConsumedEvent(RiskEvent):
    """
    Reserved capital has been consumed by downstream execution.
    """

    event_name: ClassVar[str] = "risk.capital_reservation.consumed"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    intent_id: IntentId
    strategy_id: StrategyId
