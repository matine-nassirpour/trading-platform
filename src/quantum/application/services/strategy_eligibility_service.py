from quantum.domain.risk.lifecycle.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.risk.lifecycle.strategy_eligibility_result import (
    StrategyEligibilityResult,
)
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


class StrategyEligibilityService:
    """
    Application service wrapping domain eligibility policy.
    """

    @staticmethod
    def check(
        *,
        lifecycle: StrategyLifecycle,
        at: EpochMs,
    ) -> StrategyEligibilityResult:

        return StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=at,
        )
