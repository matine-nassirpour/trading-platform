from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.handlers.command_handler import CommandHandler
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
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class EvaluateDecisionHandler(CommandHandler[EvaluateDecisionCommand, None]):
    """
    Core application handler for evaluating a decision.
    """

    def __init__(
        self,
        *,
        policy_repository: DecisionPolicyRepository,
        lifecycle_repository: StrategyLifecycleRepository,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._policy_repository = policy_repository
        self._lifecycle_repository = lifecycle_repository
        self._store = store
        self._bus = bus
        self._clock = clock
        self._ids = ids

    def handle(self, command: EvaluateDecisionCommand) -> CommandResult[None]:

        lifecycle = self._lifecycle_repository.get_lifecycle(
            command.decision_identity.strategy_id
        )

        eligibility = StrategyEligibilityPolicy.evaluate(
            lifecycle=lifecycle,
            at=self._clock.now_epoch_ms(),
        )

        if not eligibility.eligible:
            event = DecisionRejectedEvent(
                intent_id=command.intent_id,
                result=eligibility,
            )
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
                event = DecisionAuthorizedEvent(
                    intent_id=command.intent_id,
                    result=result,
                )
            else:
                event = DecisionRejectedEvent(
                    intent_id=command.intent_id,
                    result=result,
                )

        envelope = EventEnvelope(
            id=self._ids.new_event_id(),
            sequence=EventSequence.initial().next(),
            occurred_at=self._clock.now_epoch_ms(),
            recorded_at=self._clock.now_epoch_ms(),
            event=event,
            metadata=EventMetadata(
                actor_id=ActorId("system:decision_engine"),
                correlation_id=self._ids.new_correlation_id(),
                causation_id=CausationId.root(),
            ),
        )

        self._store.append([envelope])
        self._bus.publish(envelope)

        return CommandResult()
