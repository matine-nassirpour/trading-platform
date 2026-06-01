from dataclasses import dataclass

from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.risk_governance.risk_governance_id import RiskGovernanceId


@dataclass(frozen=True, slots=True)
class RiskGovernanceCommandResult:
    """
    Base application result for commands targeting RiskGovernance.
    """

    risk_governance_id: RiskGovernanceId


@dataclass(frozen=True, slots=True)
class InitializeRiskGovernanceResult(RiskGovernanceCommandResult):
    """
    Result for initialization workflow.
    """


@dataclass(frozen=True, slots=True)
class RegisterRealizedPnLResult(RiskGovernanceCommandResult):
    """
    Result for realized-PnL registration.

    This is an application convenience result.
    The persisted domain events remain the source of truth.
    """

    resulting_snapshot: RiskSnapshot
    active_breaches: tuple[RiskBreach, ...]
    insolvency_declared: bool


@dataclass(frozen=True, slots=True)
class ResetRiskTradingDayResult(RiskGovernanceCommandResult):
    """
    Result for trading-day reset.

    event_emitted=False means the domain command was idempotent.
    """

    event_emitted: bool
