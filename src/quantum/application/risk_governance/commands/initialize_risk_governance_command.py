from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.market.calendar.utc_date import UtcDate
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId


@dataclass(frozen=True, slots=True)
class InitializeRiskGovernanceCommand(BaseCommand):
    """
    Command: initialize one RiskGovernance aggregate stream.
    """

    risk_governance_id: RiskGovernanceId
    limits: RiskLimits
    initial_snapshot: RiskSnapshot
    trading_day: UtcDate
