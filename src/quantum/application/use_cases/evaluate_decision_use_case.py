from quantum.application.commands.evaluate_decision import EvaluateDecisionCommand
from quantum.application.factories.event_envelope_factory import EventEnvelopeFactory
from quantum.application.ports.outbound.decision_policy_repository import (
    DecisionPolicyRepository,
)
from quantum.application.ports.outbound.domain_event_publisher import EventPublisher
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.services.decision_event_service import DecisionEventService
from quantum.domain.decision.governance.decision_policy_evaluator import (
    DecisionPolicyEvaluator,
)
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class EvaluateDecisionUseCase:
    """
    Evaluates a trading decision against governance policies
    and emits the corresponding domain event.
    """

    def __init__(
        self,
        policy_repository: DecisionPolicyRepository,
        event_store: EventStore,
        event_publisher: EventPublisher,
    ) -> None:
        self._policy_repository = policy_repository
        self._event_store = event_store
        self._event_publisher = event_publisher

    def execute(self, command: EvaluateDecisionCommand) -> None:
        decision = command.decision_identity
        context = command.trading_context

        policies = self._policy_repository.policies_for(decision.strategy_id)

        final_result = None

        for policy in policies:
            result = DecisionPolicyEvaluator.evaluate(
                policy=policy,
                decision=decision,
                context=context,
            )

            if not result.authorized:
                final_result = result
                break

            final_result = result

        if final_result is None:
            raise RuntimeError(f"No policy found for strategy {decision.strategy_id}")

        domain_event = DecisionEventService.event_from_result(
            intent_id=command.intent_id,
            result=final_result,
        )

        # Sequence would normally come from infrastructure
        sequence = EventSequence.initial().next()

        envelope = EventEnvelopeFactory.create(
            event=domain_event,
            sequence=sequence,
            actor=ActorId("system:decision_engine"),
            correlation=CorrelationId.new(),
            causation=CausationId.root(),
        )

        self._event_store.append(envelope)
        self._event_publisher.publish(envelope)
