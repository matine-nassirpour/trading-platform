from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.evaluate_decision_command import (
    EvaluateDecisionCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.base_handler import CommandHandler
from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


class EvaluateDecisionHandler(CommandHandler[EvaluateDecisionCommand, None]):
    """
    Core application handler for evaluating a decision.
    """

    def __init__(
        self,
        event_store: EventStore,
        policy_repository,
        envelope_factory,
    ) -> None:
        self._event_store = event_store
        self._policy_repository = policy_repository
        self._envelope_factory = envelope_factory

    def handle(self, command: EvaluateDecisionCommand) -> CommandResult[None]:

        try:
            policy = self._policy_repository.load_for_strategy(
                command.decision_identity.strategy_id
            )

            result = policy.evaluate(
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

            envelope: EventEnvelope = self._envelope_factory.wrap(event)

            self._event_store.append([envelope])

            return CommandResult()

        except Exception as exc:
            raise DomainExecutionError(exc) from None
