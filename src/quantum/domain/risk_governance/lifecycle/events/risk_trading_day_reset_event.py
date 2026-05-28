from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)


@dataclass(frozen=True, slots=True)
class RiskTradingDayResetEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.trading_day.reset"
    event_version: ClassVar[int] = 1

    trading_day: UtcDate
