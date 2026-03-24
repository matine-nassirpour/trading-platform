from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@runtime_checkable
class DecisionPolicyRepository(Protocol):
    """
    Application port for accessing governance decision policies.
    """

    @abstractmethod
    def get_policies_for(self, strategy: StrategyId) -> DecisionPolicy | None:
        raise NotImplementedError
