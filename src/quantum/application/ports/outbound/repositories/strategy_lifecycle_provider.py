from typing import Protocol, runtime_checkable

from quantum.domain.decision.authorization.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId


@runtime_checkable
class StrategyLifecycleProvider(Protocol):
    """
    Application port for accessing strategy lifecycle state.

    Async-first contract:
    - Supports in-memory and persistent implementations.
    - Avoids future API breakage when backed by external storage.
    """

    async def get_lifecycle(
        self,
        strategy_id: StrategyId,
    ) -> StrategyLifecycle | None:
        raise NotImplementedError
