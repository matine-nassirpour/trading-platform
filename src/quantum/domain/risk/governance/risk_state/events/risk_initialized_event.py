from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.governance.limits.risk_limits import RiskLimits
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class RiskInitializedEvent(RiskEvent):
    """
    Emitted to initialize the RiskState aggregate.

    This event is the SINGLE source of truth for:
    - the configured RiskLimits
    - the initial Equity baseline
    - the initial Equity peak (== initial equity)
    """

    event_name: ClassVar[str] = "risk.governance.initialized"
    event_version: ClassVar[int] = 1

    limits: RiskLimits
    initial_equity: Equity
