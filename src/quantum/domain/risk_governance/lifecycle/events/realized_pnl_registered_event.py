from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.lifecycle.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RealizedPnLRegisteredEvent(RiskGovernanceEvent):
    event_name: ClassVar[str] = "risk_governance.realized_pnl.registered"
    event_version: ClassVar[int] = 1

    pnl: RealizedPnL
