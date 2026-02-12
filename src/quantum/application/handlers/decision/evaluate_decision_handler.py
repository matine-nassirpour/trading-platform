from collections.abc import Iterable
from typing import Final

from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.application.ports.outbound.repositories.decision_policy_repository import (
    DecisionPolicyRepository,
)
from quantum.application.ports.outbound.repositories.strategy_lifecycle_repository import (
    StrategyLifecycleRepository,
)
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.governance.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.risk.lifecycle.strategy_eligibility_policy import (
    StrategyEligibilityPolicy,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class EvaluateDecisionHandler(
    EventSourcedCommandHandler[EvaluateDecisionCommand, None, None]
):
    """
    Evaluates a trading decision under:

    1. Strategy lifecycle eligibility
    2. Governance decision policy
    """

    _ACTOR: Final[str] = "system:decision_engine"

    def __init__(
        self,
        *,
        policy_repository: DecisionPolicyRepository,
        lifecycle_repository: StrategyLifecycleRepository,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._policy_repository = policy_repository
        self._lifecycle_repository = lifecycle_repository

    def _stream_id(self, command: EvaluateDecisionCommand) -> str:
        return f"decision-{command.intent_id.value}"

    def _load_aggregate(self, command: EvaluateDecisionCommand):
        # This use case does not operate on an aggregate instance.
        return None

    def _execute_domain(
        self,
        *,
        command: EvaluateDecisionCommand,
        aggregate,
    ) -> tuple[Iterable[BaseEvent], None]:

        # --- Strategy lifecycle eligibility
        lifecycle = self._lifecycle_repository.get_lifecycle(
            command.decision_identity.strategy_id
        )

        eligibility = StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=self._clock.now_epoch_ms(),
        )

        if not eligibility.eligible:
            return (
                [
                    DecisionRejectedEvent(
                        intent_id=command.intent_id,
                        result=eligibility,
                    )
                ],
                None,
            )

        # --- Governance decision policy
        policy = self._policy_repository.get_policies_for(
            command.decision_identity.strategy_id
        )

        result = DecisionPolicyEvaluator.evaluate(
            policy=policy,
            decision=command.decision_identity,
            context=command.trading_context,
        )

        if result.authorized:
            return (
                [
                    DecisionAuthorizedEvent(
                        intent_id=command.intent_id,
                        result=result,
                    )
                ],
                None,
            )

        return (
            [
                DecisionRejectedEvent(
                    intent_id=command.intent_id,
                    result=result,
                )
            ],
            None,
        )
