from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.capital_management.events.capital_management_event import (
    CapitalManagementEvent,
)
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.capital_management.reservation.reason_codes.capital_release_reason_code import (
    CapitalReleaseReasonCode,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class CapitalReleasedEvent(CapitalManagementEvent):
    """
    Previously reserved capital has been released.
    """

    event_name: ClassVar[str] = "capital_management.capital.released"
    event_version: ClassVar[int] = 1

    reservation_id: CapitalReservationId
    decision_id: DecisionId
    strategy_id: StrategyId
    reason_code: CapitalReleaseReasonCode
