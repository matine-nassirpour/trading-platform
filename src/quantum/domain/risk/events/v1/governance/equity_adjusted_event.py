from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class EquityAdjustedEvent(RiskEvent):
    """
    Emitted whenever equity is adjusted by a realized PnL.

    This is the SINGLE source of truth for equity evolution.
    """

    event_name: ClassVar[str] = "risk.equity.adjusted"
    event_version: ClassVar[int] = 1

    pnl: RealizedPnL
    new_equity: Equity
    new_equity_peak: Equity
