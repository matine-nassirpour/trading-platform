from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId


@dataclass(frozen=True, slots=True)
class ResetRiskTradingDayCommand(BaseCommand):
    """
    Command: reset daily risk counters for a new trading day.
    """

    risk_governance_id: RiskGovernanceId
    trading_day: UtcDate
