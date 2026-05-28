from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.position_sizing.lifecycle.events.position_sizing_event import (
    PositionSizingEvent,
)
from quantum.domain.position_sizing.model.result.position_sizing_result import (
    PositionSizingResult,
)
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class PositionSizedEvent(PositionSizingEvent):
    event_name: ClassVar[str] = "position_sizing.sized"
    event_version: ClassVar[int] = 1

    sizing_id: PositionSizingId
    decision_id: DecisionId
    strategy_id: StrategyId
    result: PositionSizingResult
