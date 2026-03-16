from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)
from quantum.domain.shared_kernel.events.base.fact_event import FactEvent
from quantum.domain.shared_kernel.identifiers.strategy_id import StrategyId


@dataclass(frozen=True, slots=True)
class StrategyLifecycleChangedEvent(FactEvent):
    """
    Emitted whenever a strategy lifecycle state changes.
    """

    event_name: ClassVar[str] = "decision.strategy.lifecycle_changed"
    event_version: ClassVar[int] = 1

    strategy_id: StrategyId
    previous: StrategyLifecycleState
    current: StrategyLifecycleState
