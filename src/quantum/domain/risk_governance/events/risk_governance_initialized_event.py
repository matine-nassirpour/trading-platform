from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.states.risk_snapshot import RiskSnapshot


@dataclass(frozen=True, slots=True)
class RiskGovernanceInitializedEvent(RiskGovernanceEvent):
    """
    Emitted to initialize the RiskGovernance aggregate.
    """

    event_name: ClassVar[str] = "risk_governance.initialized"
    event_version: ClassVar[int] = 1

    limits: RiskLimits
    initial_snapshot: RiskSnapshot
