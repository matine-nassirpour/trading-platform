from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.risk.sizing.position_sizing_id import PositionSizingId
from quantum.domain.risk.sizing.value_objects.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class PositionSizedEvent(RiskEvent):
    event_name: ClassVar[str] = "risk.sizing.sized"
    event_version: ClassVar[int] = 1

    sizing_id: PositionSizingId
    decision_id: DecisionId
    strategy_id: StrategyId
    result: PositionSizingResult
