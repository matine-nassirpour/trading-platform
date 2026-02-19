from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
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
    ) -> DecisionAuthorizationReasonCode | None:
        if not lifecycle.validity.is_valid_at(at):
            return DecisionAuthorizationReasonCode.strategy_lifecycle_invalid()

        if not lifecycle.state.is_authorized():
            return DecisionAuthorizationReasonCode.strategy_not_authorized()

        return None
