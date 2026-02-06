from abc import ABC, abstractmethod
from collections.abc import Iterable

from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.identity.strategy_id import StrategyId


class DecisionPolicyRepository(ABC):
    """
    Application port for accessing governance decision policies.
    """

    @abstractmethod
    def policies_for(self, strategy: StrategyId) -> Iterable[DecisionPolicy]:
        raise NotImplementedError
