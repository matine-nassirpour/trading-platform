from typing import Protocol, runtime_checkable

from quantum.domain.decision.authorization.decision_policy import DecisionPolicy
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@runtime_checkable
class DecisionPolicyRepository(Protocol):
    """
    Application port for accessing governance decision policies.
    """

    def get_policies_for(self, strategy: StrategyId) -> DecisionPolicy | None:
        raise NotImplementedError
