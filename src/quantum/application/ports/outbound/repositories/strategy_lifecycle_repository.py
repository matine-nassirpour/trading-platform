from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.decision.authorization.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@runtime_checkable
class StrategyLifecycleRepository(Protocol):

    @abstractmethod
    def get_lifecycle(self, strategy_id: StrategyId) -> StrategyLifecycle | None:
        raise NotImplementedError
