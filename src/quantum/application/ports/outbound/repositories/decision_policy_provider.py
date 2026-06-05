from typing import Protocol, runtime_checkable

from quantum.domain.decision.authorization.decision_policy import DecisionPolicy
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@runtime_checkable
class DecisionPolicyProvider(Protocol):
    """
    Application port for accessing governance decision policies.

    Async-first contract:
    - Allows in-memory, SQL, Redis, EventStore or remote-backed implementations.
    - Prevents future contract breakage when persistence becomes asynchronous.
    """

    async def get_policies_for(
        self,
        strategy: StrategyId,
    ) -> DecisionPolicy | None: ...
