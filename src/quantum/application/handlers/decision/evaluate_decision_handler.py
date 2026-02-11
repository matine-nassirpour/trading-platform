from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.repositories.decision_policy_repository import (
    DecisionPolicyRepository,
)
from quantum.application.ports.outbound.repositories.strategy_lifecycle_repository import (
    StrategyLifecycleRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
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


class EvaluateDecisionHandler(AsyncCommandHandler[EvaluateDecisionCommand, None]):
    """
    Core application handler for evaluating a decision.
    """

    def __init__(
        self,
        *,
        policy_repository: DecisionPolicyRepository,
        lifecycle_repository: StrategyLifecycleRepository,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)
        self._policy_repository = policy_repository
        self._lifecycle_repository = lifecycle_repository

    async def handle(self, command: EvaluateDecisionCommand) -> CommandResult[None]:

        try:
            with self._uow:
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

                await persist_and_publish(
                    stream_id=f"decision-{command.intent_id.value}",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:decision_engine",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
