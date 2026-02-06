from abc import ABC, abstractmethod

from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle


class StrategyLifecycleRepository(ABC):

    @abstractmethod
    def get_lifecycle(self, strategy_id: StrategyId) -> StrategyLifecycle:
        raise NotImplementedError
