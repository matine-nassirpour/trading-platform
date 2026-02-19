from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


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
    ) -> DecisionAuthorizationResult:
        if not lifecycle.validity.is_valid_at(at):
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_lifecycle_invalid(),
                reason="Strategy lifecycle not valid",
            )

        if not lifecycle.state.is_authorized():
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_not_authorized(),
                reason=f"Strategy state '{lifecycle.state.value}' not authorized",
            )

        return DecisionAuthorizationResult.authorized(
            reason="Strategy lifecycle valid",
        )
