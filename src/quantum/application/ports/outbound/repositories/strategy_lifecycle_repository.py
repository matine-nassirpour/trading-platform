from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle


@runtime_checkable
class StrategyLifecycleRepository(Protocol):

    @abstractmethod
    def get_lifecycle(self, strategy_id: StrategyId) -> StrategyLifecycle:
        raise NotImplementedError
