from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent


@dataclass(frozen=True, slots=True)
class TradingDecisionAuthorizedEvent(DecisionEvent):
    """
    Emitted when a trade-candidate decision is authorized for downstream use.
    """

    event_name: ClassVar[str] = "decision.trading_decision.authorized"
    event_version: ClassVar[int] = 1
