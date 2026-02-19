from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.risk.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.primitives.domain_service import DomainService
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


class StrategyEligibilityPolicy(DomainService):
    """
    Domain Service evaluating whether a strategy is eligible
    to produce trading decisions.

    Formal domain question answered:
        "Is this strategy allowed to produce decisions at this time?"
    """

    __slots__ = ()

    @staticmethod
    def evaluate(
        *,
        lifecycle: StrategyLifecycle,
        at: EpochMs,
    ) -> DecisionAuthorizationResult:

        # Temporal validity violation
        if not lifecycle.validity.is_valid_at(at):
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_lifecycle_invalid()
            )

        # Lifecycle state violation
        if not lifecycle.state.is_authorized():
            return DecisionAuthorizationResult.rejected(
                reason_code=DecisionAuthorizationReasonCode.strategy_not_authorized()
            )

        return DecisionAuthorizationResult.authorized()
