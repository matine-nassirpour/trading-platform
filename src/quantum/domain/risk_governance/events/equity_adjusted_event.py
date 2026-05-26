from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk_governance.events.risk_governance_event import (
    RiskGovernanceEvent,
)
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class EquityAdjustedEvent(RiskGovernanceEvent):
    """
    Emitted whenever equity is adjusted by a realized PnL.

    This is the SINGLE source of truth for equity evolution.
    """

    event_name: ClassVar[str] = "risk_governance.equity.adjusted"
    event_version: ClassVar[int] = 1

    pnl: RealizedPnL
    new_equity: Equity
    new_equity_peak: Equity
