from quantum.application.ports.outbound.repositories.strategy_lifecycle_repository import (
    StrategyLifecycleRepository,
)
from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.risk.lifecycle.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


class StrategyEligibilityService:

    def __init__(self, repo: StrategyLifecycleRepository) -> None:
        self._repo = repo

    def evaluate(self, strategy_id: StrategyId, at: EpochMs):
        lifecycle = self._repo.get_lifecycle(strategy_id)

        return StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=at,
        )
