from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.capital.reservation.aggregate import CapitalReservationId
from quantum.domain.risk.capital.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalReservationRejectedEvent(RiskEvent):
    """
    Reservation request has been rejected by risk/capital policy.
    """

    event_name: ClassVar[str] = "risk.capital_reservation.rejected"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    intent_id: IntentId
    strategy_id: StrategyId
    reason_code: CapitalReservationRejectionReasonCode
