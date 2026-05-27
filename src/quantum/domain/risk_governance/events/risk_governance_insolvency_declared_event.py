from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.risk_governance.measures.equity import Equity


@dataclass(frozen=True, slots=True)
class RiskGovernanceInsolvencyDeclaredEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.insolvency.declared"
    event_version: ClassVar[int] = 1

    equity: Equity
