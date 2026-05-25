from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.common.events.risk_event import RiskEvent
from quantum.domain.risk.sizing.position_sizing_id import PositionSizingId
from quantum.domain.risk.sizing.reason_codes.position_sizing_rejection_reason_code import (
    PositionSizingRejectionReasonCode,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class PositionSizingRejectedEvent(RiskEvent):
    event_name: ClassVar[str] = "risk.sizing.rejected"
    event_version: ClassVar[int] = 1

    sizing_id: PositionSizingId
    decision_id: DecisionId
    strategy_id: StrategyId
    reason_code: PositionSizingRejectionReasonCode
