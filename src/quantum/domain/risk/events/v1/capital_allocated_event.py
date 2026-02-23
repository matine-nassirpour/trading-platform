from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.capital.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class CapitalAllocatedEvent(RiskEvent):

    event_name: ClassVar[str] = "risk.capital.allocated"
    event_version: ClassVar[int] = 1

    strategy_id: StrategyId
    allocation: CapitalAllocationIntent
