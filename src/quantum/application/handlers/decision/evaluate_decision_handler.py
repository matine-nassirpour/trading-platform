from typing import Final

from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.repositories.decision_policy_repository import (
    DecisionPolicyRepository,
)
from quantum.application.ports.outbound.repositories.strategy_lifecycle_repository import (
    StrategyLifecycleRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_events_transactionally
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
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class EvaluateDecisionHandler(CommandHandler[EvaluateDecisionCommand, None]):
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
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(outbox=outbox, uow=uow, store=store, clock=clock, ids=ids)
        self._policy_repository = policy_repository
        self._lifecycle_repository = lifecycle_repository

    def _execute(self, command: EvaluateDecisionCommand) -> None:

        try:
            stream_id = f"decision-{command.intent_id.value}"

            # --- Optimistic concurrency guard
            current_version: EventSequence = self._store.current_sequence(stream_id)

            # --- Lifecycle eligibility evaluation
            lifecycle = self._lifecycle_repository.get_lifecycle(
                command.decision_identity.strategy_id
            )

            eligibility = StrategyEligibilityPolicy.evaluate(
                lifecycle=lifecycle,
                at=self._clock.now_epoch_ms(),
            )

            if not eligibility.eligible:
                domain_events = [
                    DecisionRejectedEvent(
                        intent_id=command.intent_id,
                        result=eligibility,
                    )
                ]

            else:
                policy = self._policy_repository.get_policies_for(
                    command.decision_identity.strategy_id
                )

                result = DecisionPolicyEvaluator.evaluate(
                    policy=policy,
                    decision=command.decision_identity,
                    context=command.trading_context,
                )

                if result.authorized:
                    domain_events = [
                        DecisionAuthorizedEvent(
                            intent_id=command.intent_id,
                            result=result,
                        )
                    ]
                else:
                    domain_events = [
                        DecisionRejectedEvent(
                            intent_id=command.intent_id,
                            result=result,
                        )
                    ]

            # --- Transactional persistence (EventStore + Outbox)
            persist_events_transactionally(
                stream_id=stream_id,
                events=domain_events,
                store=self._store,
                outbox=self._outbox,
                uow=self._uow,
                ids=self._ids,
                clock=self._clock,
                actor=self._ACTOR,
                expected_version=current_version,
            )

        except DomainError as error:
            raise DomainExecutionError(error) from None
