from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.events.decision_event import DecisionEvent
from quantum.domain.decision.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class StrategyLifecycleChangedEvent(DecisionEvent):
    """
    Emitted whenever a strategy lifecycle state changes.
    """

    event_name: ClassVar[str] = "decision.strategy.lifecycle_changed"
    event_version: ClassVar[int] = 1

    strategy_id: StrategyId
    previous: StrategyLifecycleState
    current: StrategyLifecycleState
