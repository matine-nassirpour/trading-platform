from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.trading.strategy.lifecycle.strategy_eligibility_result import (
    StrategyEligibilityResult,
)
from quantum.domain.trading.strategy.lifecycle.strategy_lifecycle import (
    StrategyLifecycle,
)


class StrategyEligibilityPolicy:
    """
    Canonical policy evaluating whether a strategy is eligible
    to produce trading decisions.
    """

    @staticmethod
    def evaluate(
        *,
        lifecycle: StrategyLifecycle,
        at: EpochMs,
    ) -> StrategyEligibilityResult:
        if not lifecycle.validity.is_valid_at(at):
            return StrategyEligibilityResult(
                eligible=False,
                reason="Strategy lifecycle not valid at decision time",
            )

        if not lifecycle.state.is_authorized():
            return StrategyEligibilityResult(
                eligible=False,
                reason=f"Strategy state '{lifecycle.state.value}' is not authorized",
            )

        return StrategyEligibilityResult(
            eligible=True,
            reason="Strategy eligible for decision",
        )
