from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.identity.strategy_id import StrategyId


@runtime_checkable
class DecisionPolicyRepository(Protocol):
    """
    Application port for accessing governance decision policies.
    """

    @abstractmethod
    def policies_for(self, strategy: StrategyId) -> Iterable[DecisionPolicy]:
        raise NotImplementedError
