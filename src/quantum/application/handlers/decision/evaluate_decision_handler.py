from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.services.decision_evaluation_service import (
    DecisionEvaluationService,
)
from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
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
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
        policy: DecisionPolicy,
    ) -> None:
        self._store = store
        self._bus = bus
        self._clock = clock
        self._ids = ids
        self._policy = policy
        self._service = DecisionEvaluationService()

    def handle(self, command: EvaluateDecisionCommand) -> CommandResult[None]:

        context = TradingContext.default()

        result = self._service.evaluate(
            policy=self._policy,
            decision=command.decision_identity,
            context=context,
        )

        event = (
            DecisionAuthorizedEvent(
                intent_id=command.intent_id,
                result=result,
            )
            if result.authorized
            else DecisionRejectedEvent(
                intent_id=command.intent_id,
                result=result,
            )
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
