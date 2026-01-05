from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.decision.strategy_id import StrategyId
from quantum.domain.trading.strategy.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)


@dataclass(frozen=True)
class StrategyLifecycleChangedEvent(BaseEvent):
    """
    Emitted whenever a strategy lifecycle state changes.
    """

    event_name: ClassVar[str] = "trading.strategy_lifecycle_changed"
    event_version: ClassVar[int] = 1

    strategy_id: StrategyId
    previous: StrategyLifecycleState
    current: StrategyLifecycleState
